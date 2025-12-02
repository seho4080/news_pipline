# news_processor.py
import os, json, re, time, logging, datetime, signal, sys, csv
from urllib.parse import quote
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaException, Producer
from psycopg2.pool import SimpleConnectionPool
import psycopg2
import requests
from dateutil import parser as date_parser
from preprocess import Preprocess  # 기존 전처리 그대로 사용

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("news-processor")

# 글로벌 통계
stats = {
    'total_consumed': 0,
    'total_processed': 0,
    'db_success': 0,
    'db_failed': 0,
    'es_success': 0,
    'es_failed': 0,
    'preprocess_failed': 0,
    'json_decode_failed': 0,
    'start_time': None,
    'by_category': {},
    'last_save_count': 0  # 마지막 저장 시점의 처리 건수
}

# 통계 저장 주기 (처리한 메시지 개수 기준)
SAVE_INTERVAL = 5  # 5개 처리할 때마다 저장

# 로그 디렉토리 및 파일 경로
# Docker 환경에서는 /app/logs, 로컬에서는 ../logs 사용
LOG_DIR = os.getenv('LOG_DIR', '/app/logs')
LOG_FILE = os.path.join(LOG_DIR, 'consumer_stats.csv')

# 로그 디렉토리 생성
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except Exception as e:
    log.warning(f"로그 디렉토리 생성 실패: {e}")

# ---- ENV
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
IN_TOPIC        = os.getenv("IN_TOPIC", "news-topic")
GROUP_ID        = os.getenv("GROUP_ID", "python-news-group")
DLQ_TOPIC       = os.getenv("DLQ_TOPIC", "news-dlq")  # 없애고 싶으면 빈 값으로

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USERNAME")
DB_PASS = os.getenv("DB_PASSWORD")
DB_MIN  = int(os.getenv("DB_MIN_CONN", "1"))
DB_MAX  = int(os.getenv("DB_MAX_CONN", "5"))
USE_PGVECTOR = os.getenv("USE_PGVECTOR", "false").lower() == "true"  # embedding 컬럼이 vector면 true

ES_BASE_URL = os.getenv("ES_BASE_URL", "http://localhost:9200")
ES_INDEX    = os.getenv("ES_INDEX", "news")
ES_AUTH     = (os.getenv("ES_USER"), os.getenv("ES_PASS")) if os.getenv("ES_USER") else None
ES_TIMEOUT  = int(os.getenv("ES_TIMEOUT", "10"))

# ---- Helpers
def parse_date(s: str) -> datetime.datetime:
    if not s:
        return datetime.datetime(1990,1,1)
    try:
        return date_parser.parse(s)
    except Exception:
        return datetime.datetime(1990,1,1)

def extract_writer(content: str) -> str:
    m = re.search(r'([가-힣]{2,4})\s?기자', content or '')
    return m.group(1) if m else "연합뉴스"

def insert_article(pool, row):
    """
    row keys: title, writer, write_date(dt), category, content, url, keywords(any), embedding(list[float])
    트랜잭션 안전성을 보장하며 DB에 삽입
    """
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            if USE_PGVECTOR:
                # embedding 컬럼이 pgvector(vector) 라고 가정
                # psycopg2는 파이썬 list를 바로 vector로 캐스팅 못하므로 text로 전달 후 CAST 하거나
                # pgvector 어댑터를 사용하세요. 여기선 간단히 ARRAY로 저장하는 방법을 예시.
                cur.execute("""
                    INSERT INTO news_article
                        (title, writer, write_date, category, content, url, keywords, embedding)
                    VALUES (%s,%s,%s,%s,%s,%s,%s, %s::vector)
                    ON CONFLICT (url) DO NOTHING
                """, (
                    row["title"], row["writer"], row["write_date"], row["category"],
                    row["content"], row["url"],
                    json.dumps(row["keywords"], ensure_ascii=False) if not isinstance(row["keywords"], str) else row["keywords"],
                    f"[{', '.join(str(x) for x in row['embedding'])}]"
                ))
            else:
                # embedding을 jsonb(text)나 float[]로 보관하는 경우(간단)
                cur.execute("""
                    INSERT INTO news_article
                        (title, writer, write_date, category, content, url, keywords, embedding, updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s, CURRENT_TIMESTAMP)
                    ON CONFLICT (url) DO NOTHING
                """, (
                    row["title"], row["writer"], row["write_date"], row["category"],
                    row["content"], row["url"],
                    json.dumps(row["keywords"], ensure_ascii=False) if not isinstance(row["keywords"], str) else row["keywords"],
                    json.dumps(row["embedding"])  # jsonb 컬럼 권장
                ))
        conn.commit()
    except Exception as e:
        # 트랜잭션 롤백
        try:
            conn.rollback()
            log.error(f"DB 삽입 실패, 롤백 완료: {e}")
        except Exception as rollback_error:
            log.error(f"롤백 실패: {rollback_error}")
        raise  # 예외를 다시 발생시켜 호출자가 처리하도록
    finally:
        # 커넥션 상태 확인 후 풀에 반환
        try:
            if conn.closed:
                log.warning("커넥션이 닫혀있음, 새 커넥션 필요")
            pool.putconn(conn)
        except Exception as e:
            log.error(f"커넥션 풀 반환 실패: {e}")

def upsert_es(session: requests.Session, doc: dict, doc_id: str):
    """
    단순 PUT upsert. (필요시 _update API, pipeline, bulk 등으로 확장)
    """
    url = f"{ES_BASE_URL.rstrip('/')}/{ES_INDEX}/_doc/{doc_id}"
    r = session.put(url, json=doc, timeout=ES_TIMEOUT, auth=ES_AUTH)
    if not r.ok:
        raise RuntimeError(f"ES upsert failed: {r.status_code} {r.text[:200]}")

def save_statistics_to_csv():
    """통계를 CSV 파일에 저장"""
    try:
        log.info(f"📝 CSV 저장 시도: {LOG_FILE}")
        log.info(f"📂 LOG_DIR exists: {os.path.exists(LOG_DIR)}")
        
        # 파일이 없으면 헤더 작성
        write_header = not os.path.exists(LOG_FILE)
        log.info(f"✍️ Write header: {write_header}")
        
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if write_header:
                writer.writerow([
                    '종료시각', '실행시간(초)', '소비_메시지', '전처리_성공', 
                    'DB_성공', 'DB_실패', 'DB_성공률(%)',
                    'ES_성공', 'ES_실패', 'ES_성공률(%)',
                    'JSON_디코드_실패', '전처리_실패',
                    '카테고리별_상세'
                ])
            
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            runtime = int(time.time() - stats['start_time']) if stats['start_time'] else 0
            
            db_rate = 0
            if stats['db_success'] + stats['db_failed'] > 0:
                db_rate = (stats['db_success'] / (stats['db_success'] + stats['db_failed'])) * 100
            
            es_rate = 0
            if stats['es_success'] + stats['es_failed'] > 0:
                es_rate = (stats['es_success'] / (stats['es_success'] + stats['es_failed'])) * 100
            
            # 카테고리별 상세 정보를 JSON 형태로
            category_details = json.dumps(stats['by_category'], ensure_ascii=False)
            
            writer.writerow([
                timestamp,
                runtime,
                stats['total_consumed'],
                stats['total_processed'],
                stats['db_success'],
                stats['db_failed'],
                f"{db_rate:.2f}",
                stats['es_success'],
                stats['es_failed'],
                f"{es_rate:.2f}",
                stats['json_decode_failed'],
                stats['preprocess_failed'],
                category_details
            ])
        
        log.info(f"✅ 통계가 파일에 저장됨: {LOG_FILE}")
    except Exception as e:
        log.error(f"❌ CSV 파일 저장 실패: {e}", exc_info=True)

def print_final_statistics():
    """종료 시 최종 통계 출력"""
    log.info("\n" + "="*70)
    log.info("📊 뉴스 Consumer 최종 통계")
    log.info("="*70)
    
    if stats['start_time']:
        runtime = time.time() - stats['start_time']
        hours, remainder = divmod(int(runtime), 3600)
        minutes, seconds = divmod(remainder, 60)
        log.info(f"⏱️  총 실행 시간: {hours}시간 {minutes}분 {seconds}초")
    
    log.info(f"📥 총 소비 메시지: {stats['total_consumed']}개")
    log.info(f"✅ 전처리 성공: {stats['total_processed']}개")
    log.info(f"❌ JSON 디코드 실패: {stats['json_decode_failed']}개")
    log.info(f"❌ 전처리 실패: {stats['preprocess_failed']}개")
    
    log.info(f"\n💾 PostgreSQL:")
    log.info(f"  ✅ 삽입 성공: {stats['db_success']}개")
    log.info(f"  ❌ 삽입 실패: {stats['db_failed']}개")
    if stats['db_success'] + stats['db_failed'] > 0:
        db_rate = (stats['db_success'] / (stats['db_success'] + stats['db_failed'])) * 100
        log.info(f"  📈 성공률: {db_rate:.2f}%")
    
    log.info(f"\n🔍 Elasticsearch:")
    log.info(f"  ✅ 색인 성공: {stats['es_success']}개")
    log.info(f"  ❌ 색인 실패: {stats['es_failed']}개")
    if stats['es_success'] + stats['es_failed'] > 0:
        es_rate = (stats['es_success'] / (stats['es_success'] + stats['es_failed'])) * 100
        log.info(f"  📈 성공률: {es_rate:.2f}%")
    
    if stats['by_category']:
        log.info("\n📂 카테고리별 통계:")
        log.info("-" * 70)
        for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
            log.info(f"  {category:12s} | {count:4d}개")
    
    log.info("="*70)
    log.info("👋 Consumer 종료")
    log.info("="*70 + "\n")

def signal_handler(signum, frame):
    """시그널 핸들러 (Ctrl+C 처리)"""
    log.info("\n⚠️  종료 신호 감지됨 (Ctrl+C)")
    save_statistics_to_csv()
    print_final_statistics()
    sys.exit(0)

def main():
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    stats['start_time'] = time.time()
    
    # 프로그램 시작 시 초기 CSV 파일 생성 (헤더만)
    save_statistics_to_csv()
    
    # Kafka consumer(수동 커밋)
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "max.poll.interval.ms": 600000,
    })
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP}) if DLQ_TOPIC else None

    # DB pool
    pool = SimpleConnectionPool(DB_MIN, DB_MAX, host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

    # ES session
    session = requests.Session()

    # 전처리기
    gpt = Preprocess()

    consumer.subscribe([IN_TOPIC])
    log.info("🚀 뉴스 Consumer 시작")
    log.info(f"설정: Kafka={KAFKA_BOOTSTRAP}, Topic={IN_TOPIC}, DB={DB_HOST}/{DB_NAME}, ES={ES_INDEX}")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaException._PARTITION_EOF:
                    log.error(f"Kafka error: {msg.error()}")
                continue

            stats['total_consumed'] += 1
            
            try:
                data = json.loads(msg.value().decode("utf-8"))
            except Exception as e:
                stats['json_decode_failed'] += 1
                log.exception("JSON 디코드 실패")
                if producer:
                        if producer is not None and DLQ_TOPIC:
                            producer.produce(DLQ_TOPIC, msg.value())  # 원문 보관
                consumer.commit(msg)  # 소비 불가 → 건너뜀
                continue

            # 원본 필드
            title = (data.get("title") or "제목 없음").strip()
            url   = (data.get("url") or "").strip()
            content_raw = (data.get("content") or "").strip()
            write_date  = parse_date(data.get("write_date"))

            # 전처리
            try:
                content   = gpt.preprocess_content(content_raw)
                writer    = extract_writer(content)
                keywords  = gpt.transform_extract_keywords(content)
                category  = gpt.transform_classify_category(content)
                embedding = gpt.transform_to_embedding(content)
                stats['total_processed'] += 1
            except Exception as e:
                stats['preprocess_failed'] += 1
                log.exception(f"전처리 실패 url={url}")
                if producer:
                        if producer is not None and DLQ_TOPIC:
                            producer.produce(DLQ_TOPIC, json.dumps({"reason":"preprocess_error","raw":data}, ensure_ascii=False).encode("utf-8"))
                consumer.commit(msg)
                continue

            row = {
                "title": title,
                "writer": writer,
                "write_date": write_date,
                "category": category,
                "content": content,
                "url": url,
                "keywords": keywords,
                "embedding": embedding,
            }

            # 카테고리별 통계 업데이트
            if category not in stats['by_category']:
                stats['by_category'][category] = 0
            stats['by_category'][category] += 1
            
            # 1) Postgres INSERT (성공해야 다음 단계로)
            try:
                insert_article(pool, row)
                stats['db_success'] += 1
            except Exception as e:
                stats['db_failed'] += 1
                log.exception(f"DB 삽입 실패 url={url} → 재시도(커밋 안함)")
                time.sleep(1)
                continue  # 커밋 X → 재처리

            # 2) Elasticsearch upsert
            try:
                doc_id = quote(url, safe="")
                doc = {
                    "title": row["title"],
                    "writer": row["writer"],
                    "write_date": row["write_date"].isoformat(),
                    "category": row["category"],
                    "content": row["content"],
                    "url": row["url"],
                    "keywords": row["keywords"],
                    "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
                }
                upsert_es(session, doc, doc_id)
                stats['es_success'] += 1
            except Exception as e:
                stats['es_failed'] += 1
                # ES 실패 시 선택지:
                # - 커밋하지 않고 재시도(정합↑, 정체 가능)
                # - DLQ로 보내고 커밋(정합↓, 유실 방지)
                log.exception(f"ES 색인 실패 url={url} → DLQ 후 커밋")
                if producer:
                        if producer is not None and DLQ_TOPIC:
                            producer.produce(DLQ_TOPIC, json.dumps({"reason":"es_upsert_failed","row":doc}, ensure_ascii=False).encode("utf-8"))
                # 여긴 정책적으로 커밋(필요시 전략 변경)
                consumer.commit(msg)
                continue

            # 3) 성공적으로 PG+ES 처리 완료 → 오프셋 커밋
            consumer.commit(msg)
            log.info(f"✔ stored & indexed: {title}")
            
            # 주기적으로 통계 저장 (5개 처리할 때마다)
            if stats['total_consumed'] - stats['last_save_count'] >= SAVE_INTERVAL:
                save_statistics_to_csv()
                stats['last_save_count'] = stats['total_consumed']
                log.info(f"📊 중간 통계 저장 완료 (처리: {stats['total_consumed']}개)")

    except KeyboardInterrupt:
        log.info("\n⚠️  사용자에 의해 중단됨")
        save_statistics_to_csv()
        print_final_statistics()
    finally:
        log.info("리소스 정리 중...")
        consumer.close()
        if producer: producer.flush(5)
        session.close()
        pool.closeall()
        log.info("리소스 정리 완료")

if __name__ == "__main__":
    main()
