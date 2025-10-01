# news_processor.py
import os, json, re, datetime, time, logging
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaException, Producer
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from consumer.preprocess import Preprocess  # 기존 그대로 사용

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("news-processor")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
IN_TOPIC  = os.getenv("IN_TOPIC", "news-topic")
OUT_TOPIC = os.getenv("OUT_TOPIC", "")  # 선택: 가공본 재발행
GROUP_ID  = os.getenv("GROUP_ID", "python-news-group")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USERNAME")
DB_PASS = os.getenv("DB_PASSWORD")

def parse_date(s: str) -> datetime.datetime:
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%a, %d %b %Y %H:%M:%S %z'):
        try: return datetime.datetime.strptime(s, fmt)
        except ValueError: pass
    return datetime.datetime(1990,1,1)

def extract_writer(content: str) -> str:
    m = re.search(r'([가-힣]{2,4})\s?기자', content or '')
    return m.group(1) if m else "연합뉴스"

def insert_article(pool, row):
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO news_article
                    (title, writer, write_date, category, content, url, keywords, embedding)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (url) DO NOTHING
            """, (
                row["title"],
                row["writer"],
                row["write_date"],
                row["category"],
                row["content"],
                row["url"],
                # keywords: TEXT[] 또는 JSON/text 컬럼이면 형식에 맞게 변환
                row["keywords"] if isinstance(row["keywords"], str) else json.dumps(row["keywords"], ensure_ascii=False),
                row["embedding"],  # pgvector면 CAST 필요
            ))
        conn.commit()
    finally:
        pool.putconn(conn)

def main():
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,   # DB 성공 후 수동 커밋
        "max.poll.interval.ms": 600000
    })
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP}) if OUT_TOPIC else None
    pool = SimpleConnectionPool(1, 5, host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    gpt = Preprocess()

    consumer.subscribe([IN_TOPIC])
    log.info(f"Consuming from {IN_TOPIC}")

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
                log.exception("JSON 디코드 실패, 스킵")
                consumer.commit(msg)
                continue

            title = (data.get("title") or "제목 없음").strip()
            url = data.get("url") or ""
            write_date_str = data.get("write_date") or "2025-04-18 00:00:00"
            origin = (data.get("content") or "").strip()

            try:
                content   = gpt.preprocess_content(origin)
                writer    = extract_writer(content)
                keywords  = gpt.transform_extract_keywords(content)
                category  = gpt.transform_classify_category(content)
                embedding = gpt.transform_to_embedding(content)
                write_dt  = parse_date(write_date_str)
            except Exception as e:
                log.exception(f"전처리 실패 url={url}, DLQ로 보낼 수 있으면 보내고 커밋")
                consumer.commit(msg)
                continue

            row = {
                "title": title, "writer": writer, "write_date": write_dt,
                "category": category, "content": content, "url": url,
                "keywords": keywords, "embedding": embedding
            }

            # DB 저장 → 성공 시에만 커밋
            try:
                insert_article(pool, row)
            except Exception as e:
                log.exception(f"DB 삽입 실패 url={url}, 재시도 대기")
                time.sleep(1)       # 간단 백오프
                continue            # 커밋하지 않음 → 다시 처리됨

            # (선택) 가공본 재발행
            if producer and OUT_TOPIC:
                payload = {
                    **{k: v for k, v in row.items() if k != "write_date"},
                    "write_date": write_dt.isoformat()
                }
                producer.produce(OUT_TOPIC, json.dumps(payload, ensure_ascii=False).encode("utf-8"))
                producer.poll(0)

            consumer.commit(msg)

    finally:
        consumer.close()
        if producer: producer.flush(5)
        pool.closeall()

if __name__ == "__main__":
    main()