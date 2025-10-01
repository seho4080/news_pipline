# news_processor.py
import os, json, re, time, logging, datetime
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
                        (title, writer, write_date, category, content, url, keywords, embedding)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (url) DO NOTHING
                """, (
                    row["title"], row["writer"], row["write_date"], row["category"],
                    row["content"], row["url"],
                    json.dumps(row["keywords"], ensure_ascii=False) if not isinstance(row["keywords"], str) else row["keywords"],
                    json.dumps(row["embedding"])  # jsonb 컬럼 권장
                ))
        conn.commit()
    finally:
        pool.putconn(conn)

def upsert_es(session: requests.Session, doc: dict, doc_id: str):
    """
    단순 PUT upsert. (필요시 _update API, pipeline, bulk 등으로 확장)
    """
    url = f"{ES_BASE_URL.rstrip('/')}/{ES_INDEX}/_doc/{doc_id}"
    r = session.put(url, json=doc, timeout=ES_TIMEOUT, auth=ES_AUTH)
    if not r.ok:
        raise RuntimeError(f"ES upsert failed: {r.status_code} {r.text[:200]}")

def main():
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
    log.info(f"Consuming from {IN_TOPIC}; writing to Postgres & ES(index={ES_INDEX})")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaException._PARTITION_EOF:
                    log.error(f"Kafka error: {msg.error()}")
                continue

            try:
                data = json.loads(msg.value().decode("utf-8"))
            except Exception as e:
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
            except Exception as e:
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

            # 1) Postgres INSERT (성공해야 다음 단계로)
            try:
                insert_article(pool, row)
            except Exception as e:
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
            except Exception as e:
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

    finally:
        consumer.close()
        if producer: producer.flush(5)
        session.close()
        pool.closeall()

if __name__ == "__main__":
    main()
