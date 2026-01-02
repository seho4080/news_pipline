# news_processor.py
import os, json, re, time, logging, datetime, signal, sys, csv, atexit, threading, gc
from urllib.parse import quote
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaException, Producer
from psycopg2.pool import SimpleConnectionPool
import psycopg2
import requests
from dateutil import parser as date_parser
from preprocess import Preprocess  # 기존 전처리 그대로 사용

load_dotenv()

# 로깅 설정 (DEBUG 레벨 환경변수로 제어)
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger("news-processor")
log.info(f"로깅 레벨: {log_level}")

# Graceful shutdown 플래그
shutdown_event = threading.Event()

def signal_handler(signum, frame):
    """SIGTERM, SIGINT 신호 핸들러"""
    log.info(f"\n⚠️  신호 {signum} 수신 - 안전한 종료 시작...")
    shutdown_event.set()

# 신호 핸들러 등록
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

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

# 에러 샘플링 (같은 에러 반복 방지)
error_sample_count = {}
ERROR_SAMPLE_THRESHOLD = 10  # 같은 에러 10번까지만 로깅

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
DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", "10"))  # 연결 타임아웃
DB_IDLE_TIMEOUT = int(os.getenv("DB_IDLE_TIMEOUT", "600"))  # 유휴 연결 종료 시간 (10분)
USE_PGVECTOR = os.getenv("USE_PGVECTOR", "false").lower() == "true"  # embedding 컬럼이 vector면 true

ES_BASE_URL = os.getenv("ES_BASE_URL", "http://localhost:9200")
ES_INDEX    = os.getenv("ES_INDEX", "news")
ES_AUTH     = (os.getenv("ES_USER"), os.getenv("ES_PASS")) if os.getenv("ES_USER") else None
ES_TIMEOUT  = int(os.getenv("ES_TIMEOUT", "10"))

# ---- Helpers
def should_log_error(error_key: str) -> bool:
    """에러 샘플링: 같은 에러는 최대 ERROR_SAMPLE_THRESHOLD번까지만 로깅"""
    global error_sample_count
    if error_key not in error_sample_count:
        error_sample_count[error_key] = 0
    
    error_sample_count[error_key] += 1
    count = error_sample_count[error_key]
    
    # 처음 10개, 그 다음 100개마다 로깅
    if count <= ERROR_SAMPLE_THRESHOLD or count % 100 == 0:
        return True
    elif count == ERROR_SAMPLE_THRESHOLD + 1:
        log.warning(f"⚠️  같은 에러가 반복되므로 이후 {error_key} 에러는 100번마다만 로깅합니다")
    return False

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
    """통계를 CSV 파일에 저장 (timestamp 기반 upsert로 멱등성 보장)"""
    try:
        log.info(f"📝 CSV 저장 시도: {LOG_FILE}")
        
        # 현재 통계 계산
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        runtime = int(time.time() - stats['start_time']) if stats['start_time'] else 0
        
        db_rate = 0
        if stats['db_success'] + stats['db_failed'] > 0:
            db_rate = (stats['db_success'] / (stats['db_success'] + stats['db_failed'])) * 100
        
        es_rate = 0
        if stats['es_success'] + stats['es_failed'] > 0:
            es_rate = (stats['es_success'] / (stats['es_success'] + stats['es_failed'])) * 100
        
        category_details = json.dumps(stats['by_category'], ensure_ascii=False)
        
        new_row = [
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
        ]
        
        # 파일 존재 여부 확인
        file_exists = os.path.exists(LOG_FILE)
        
        if file_exists:
            # 기존 파일 읽기
            existing_rows = []
            with open(LOG_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)  # 헤더 읽기
                for row in reader:
                    existing_rows.append(row)
            
            # 같은 timestamp 행 찾기 및 업데이트 (없으면 추가)
            updated = False
            for i, row in enumerate(existing_rows):
                if row and row[0] == timestamp:
                    existing_rows[i] = new_row
                    updated = True
                    log.info(f"🔄 기존 통계 업데이트: {timestamp}")
                    break
            
            if not updated:
                existing_rows.append(new_row)
                log.info(f"➕ 새로운 통계 추가: {timestamp}")
            
            # 파일 덮어쓰기
            with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # 헤더 작성
                writer.writerow([
                    '종료시각', '실행시간(초)', '소비_메시지', '전처리_성공', 
                    'DB_성공', 'DB_실패', 'DB_성공률(%)',
                    'ES_성공', 'ES_실패', 'ES_성공률(%)',
                    'JSON_디코드_실패', '전처리_실패',
                    '카테고리별_상세'
                ])
                # 모든 행 작성
                writer.writerows(existing_rows)
        else:
            # 파일 없음 → 신규 생성
            with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '종료시각', '실행시간(초)', '소비_메시지', '전처리_성공', 
                    'DB_성공', 'DB_실패', 'DB_성공률(%)',
                    'ES_성공', 'ES_실패', 'ES_성공률(%)',
                    'JSON_디코드_실패', '전처리_실패',
                    '카테고리별_상세'
                ])
                writer.writerow(new_row)
            log.info(f"✨ 새로운 CSV 파일 생성: {LOG_FILE}")
        
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
    try:
        pool = SimpleConnectionPool(
            DB_MIN, DB_MAX,
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=DB_TIMEOUT,
            keepalives=1,
            keepalives_idle=DB_IDLE_TIMEOUT,
            options="-c statement_timeout=30000"  # 30초 쿼리 타임아웃
        )
        log.info(f"✅ DB 연결 풀 생성: {DB_MIN}-{DB_MAX} 연결, 타임아웃={DB_TIMEOUT}초")
    except Exception as e:
        log.error(f"❌ DB 연결 풀 생성 실패: {e}")
        raise

    # ES session
    session = requests.Session()

    # 전처리기
    gpt = Preprocess()

    consumer.subscribe([IN_TOPIC])
    log.info("🚀 뉴스 Consumer 시작")
    log.info(f"설정: Kafka={KAFKA_BOOTSTRAP}, Topic={IN_TOPIC}, DB={DB_HOST}/{DB_NAME}, ES={ES_INDEX}")

    try:
        while not shutdown_event.is_set():
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
                log.debug(f"원본 메시지: {msg.value()[:200]}")
                if producer:
                        if producer is not None and DLQ_TOPIC:
                            producer.produce(DLQ_TOPIC, msg.value())  # 원문 보관
                consumer.commit(msg)  # 소비 불가 → 건너뜀
                continue
            
            log.debug(f"메시지 수신: {data.get('title', 'Unknown')}")

            # 원본 필드
            title = (data.get("title") or "제목 없음").strip()
            url   = (data.get("url") or "").strip()
            content_raw = (data.get("content") or "").strip()
            write_date  = parse_date(data.get("write_date"))

            # 전처리
            try:
                log.debug(f"전처리 시작: {url}")
                content   = gpt.preprocess_content(content_raw)
                writer    = extract_writer(content)
                keywords  = gpt.transform_extract_keywords(content)
                category  = gpt.transform_classify_category(content)
                embedding = gpt.transform_to_embedding(content)
                stats['total_processed'] += 1
                log.debug(f"전처리 완료: {url} → {category}")
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
            max_retries = 3
            retry_count = 0
            db_success = False
            
            while retry_count < max_retries:
                try:
                    log.debug(f"DB 저장 시도: {url}")
                    insert_article(pool, row)
                    stats['db_success'] += 1
                    log.debug(f"DB 저장 성공: {url}")
                    db_success = True
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = min(2 ** retry_count, 10)  # 지수 백오프: 2s, 4s, 8s
                        if should_log_error("db_insert_retry"):
                            log.warning(f"DB 삽입 실패 (재시도 {retry_count}/{max_retries-1}) url={url} → {wait_time}초 대기")
                            log.debug(f"DB 오류: {str(e)}")
                        time.sleep(wait_time)
                    else:
                        stats['db_failed'] += 1
                        if should_log_error("db_insert_final"):
                            log.exception(f"DB 삽입 최종 실패 url={url} → DLQ 후 커밋")
                        if producer and DLQ_TOPIC:
                            producer.produce(DLQ_TOPIC, json.dumps({
                                "reason": "db_insert_failed",
                                "row": row,
                                "error": str(e)
                            }, ensure_ascii=False).encode("utf-8"))
                        consumer.commit(msg)
                        db_success = False
            
            if not db_success:
                continue  # DLQ 처리 후 다음 메시지로

            # 2) Elasticsearch upsert (지수 백오프 재시도 적용)
            max_es_retries = 3
            es_retry_count = 0
            es_success = False
            
            while es_retry_count < max_es_retries:
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
                    log.debug(f"ES 색인 시도: {url} (doc_id={doc_id})")
                    upsert_es(session, doc, doc_id)
                    stats['es_success'] += 1
                    log.debug(f"ES 색인 성공: {url}")
                    es_success = True
                    break
                except Exception as e:
                    es_retry_count += 1
                    if es_retry_count < max_es_retries:
                        wait_time = min(2 ** es_retry_count, 10)  # 지수 백오프: 2s, 4s, 8s
                        if should_log_error("es_upsert_retry"):
                            log.warning(f"ES 색인 실패 (재시도 {es_retry_count}/{max_es_retries-1}) url={url} → {wait_time}초 대기")
                            log.debug(f"ES 오류: {str(e)}")
                        time.sleep(wait_time)
                    else:
                        stats['es_failed'] += 1
                        if should_log_error("es_upsert_final"):
                            log.exception(f"ES 색인 최종 실패 url={url} → DLQ 후 커밋")
                        if producer and DLQ_TOPIC:
                            producer.produce(DLQ_TOPIC, json.dumps({
                                "reason": "es_upsert_failed",
                                "row": doc,
                                "error": str(e)
                            }, ensure_ascii=False).encode("utf-8"))
                        consumer.commit(msg)
                        es_success = False
            
            if not es_success:
                continue  # DLQ 처리 후 다음 메시지로

            # 3) 성공적으로 PG+ES 처리 완료 → 오프셋 커밋
            consumer.commit(msg)
            log.info(f"✔ stored & indexed: {title}")
            log.debug(f"처리 완료: url={url}, category={row['category']}")
            
            # 주기적으로 통계 저장 (5개 처리할 때마다)
            if stats['total_consumed'] - stats['last_save_count'] >= SAVE_INTERVAL:
                save_statistics_to_csv()
                stats['last_save_count'] = stats['total_consumed']
                log.info(f"📊 중간 통계 저장 완료 (처리: {stats['total_consumed']}개, DB: {stats['db_success']}/{stats['db_success']+stats['db_failed']}, ES: {stats['es_success']}/{stats['es_success']+stats['es_failed']})")
                
                # 주기적 가비지 컬렉션 (메모리 누수 방지)
                collected = gc.collect()
                log.debug(f"♻️  가비지 컬렉션 완료 (정리된 객체: {collected}개)")

    except KeyboardInterrupt:
        log.info("\n⚠️  사용자 인터럽트 - 종료 시작")
        shutdown_event.set()
    except Exception as e:
        log.error(f"❌ 메인 루프 오류: {e}", exc_info=True)
        shutdown_event.set()
    finally:
        log.info("🧹 리소스 정리 중...")
        try:
            # 최종 통계 저장
            save_statistics_to_csv()
            log.info("📊 최종 통계 저장 완료")
        except Exception as e:
            log.error(f"통계 저장 실패: {e}")
        
        # Consumer 종료 (남은 메시지 처리 X)
        consumer.close()
        log.info("✅ Consumer 종료")
        
        # Producer flush
        if producer:
            try:
                producer.flush(5)
                log.info("✅ Producer flush 완료")
            except Exception as e:
                log.error(f"Producer flush 실패: {e}")
        
        # Session 종료
        try:
            session.close()
            log.info("✅ Session 종료")
        except Exception as e:
            log.error(f"Session 종료 실패: {e}")
        
        # 연결 풀 종료
        try:
            pool.closeall()
            log.info("✅ DB 연결 풀 종료")
        except Exception as e:
            log.error(f"DB 연결 풀 종료 실패: {e}")
        
        log.info("✅ 모든 리소스 정리 완료 - 프로세스 종료")

if __name__ == "__main__":
    main()
