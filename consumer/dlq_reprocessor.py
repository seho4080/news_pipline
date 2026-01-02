#!/usr/bin/env python3
"""
DLQ (Dead Letter Queue) 메시지 재처리 스크립트
실패한 메시지를 news-dlq 토픽에서 읽어 다시 처리합니다.
"""

import json
import logging
import time
import argparse
from datetime import datetime
from urllib.parse import quote

from confluent_kafka import Consumer, Producer, KafkaError
from elasticsearch import Elasticsearch
import psycopg2
from psycopg2 import pool

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
log = logging.getLogger(__name__)

# 설정
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
DLQ_TOPIC = "news-dlq"
ELASTICSEARCH_URL = "http://elasticsearch:9200"
DB_HOST = "postgres"
DB_PORT = 5432
DB_NAME = "news_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

# 연결 풀
try:
    connection_pool = pool.SimpleConnectionPool(
        1, 5,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=5
    )
except Exception as e:
    log.error(f"❌ PostgreSQL 연결 풀 생성 실패: {e}")
    exit(1)

# Elasticsearch 클라이언트
try:
    es_session = Elasticsearch([ELASTICSEARCH_URL], timeout=10)
    es_session.info()  # 연결 테스트
    log.info(f"✅ Elasticsearch 연결 성공: {ELASTICSEARCH_URL}")
except Exception as e:
    log.error(f"❌ Elasticsearch 연결 실패: {e}")
    exit(1)

# Kafka Producer (성공한 메시지용)
producer = Producer({
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'acks': 'all'
})

def upsert_es(session, doc, doc_id):
    """Elasticsearch에 문서 upsert"""
    try:
        session.index(
            index="news",
            id=doc_id,
            body=doc,
            refresh=True
        )
        return True
    except Exception as e:
        log.error(f"❌ ES upsert 실패: {e}")
        return False

def insert_article(pool, row):
    """PostgreSQL에 기사 삽입"""
    conn = pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO articles (title, content, url, writer, write_date, category, keywords)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                writer = EXCLUDED.writer,
                write_date = EXCLUDED.write_date,
                category = EXCLUDED.category,
                keywords = EXCLUDED.keywords
        """, (
            row.get('title'),
            row.get('content'),
            row.get('url'),
            row.get('writer'),
            row.get('write_date'),
            row.get('category'),
            row.get('keywords')
        ))
        conn.commit()
        log.debug(f"✅ DB 저장: {row['url']}")
    except Exception as e:
        conn.rollback()
        log.error(f"❌ DB 저장 실패: {e}")
        raise
    finally:
        pool.putconn(conn)

def reprocess_dlq_message(msg_value):
    """DLQ 메시지 재처리"""
    try:
        data = json.loads(msg_value.decode('utf-8'))
        reason = data.get('reason')
        row = data.get('row')
        
        log.info(f"🔄 DLQ 메시지 재처리 중: {reason} - URL={row.get('url')}")
        
        # 원인별 처리
        if reason == "es_upsert_failed":
            # Elasticsearch 재시도
            try:
                doc_id = quote(row['url'], safe="")
                doc = {
                    "title": row.get("title"),
                    "writer": row.get("writer"),
                    "write_date": row.get("write_date"),
                    "category": row.get("category"),
                    "content": row.get("content"),
                    "url": row.get("url"),
                    "keywords": row.get("keywords"),
                    "updated_at": datetime.utcnow().isoformat() + "Z",
                }
                
                if upsert_es(es_session, doc, doc_id):
                    log.info(f"✅ DLQ 메시지 재처리 성공: {row['url']}")
                    return True
                else:
                    log.warning(f"⚠️  DLQ 메시지 재처리 실패 (ES): {row['url']}")
                    return False
            except Exception as e:
                log.error(f"❌ DLQ 메시지 처리 중 ES 오류: {e}")
                return False
        
        else:
            log.warning(f"⚠️  알 수 없는 실패 이유: {reason}")
            return False
            
    except json.JSONDecodeError as e:
        log.error(f"❌ JSON 파싱 실패: {e}")
        return False
    except Exception as e:
        log.error(f"❌ DLQ 메시지 처리 중 오류: {e}")
        return False

def main(group_id=None, max_messages=None):
    """DLQ 메시지 처리"""
    if group_id is None:
        group_id = f"dlq-reprocessor-{int(time.time())}"
    
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,
        'session.timeout.ms': 6000
    })
    
    consumer.subscribe([DLQ_TOPIC])
    log.info(f"✅ DLQ 컨슈머 시작: {DLQ_TOPIC} (그룹: {group_id})")
    
    processed = 0
    success = 0
    failed = 0
    
    try:
        while True:
            if max_messages and processed >= max_messages:
                log.info(f"✅ 지정된 메시지 수({max_messages}) 처리 완료")
                break
            
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    log.info("📌 토픽의 끝 도달")
                else:
                    log.error(f"❌ Kafka 오류: {msg.error()}")
                continue
            
            # 메시지 처리
            if reprocess_dlq_message(msg.value()):
                success += 1
                consumer.commit(msg)
                log.info(f"✅ 메시지 커밋 (성공: {success}, 실패: {failed})")
            else:
                failed += 1
                log.warning(f"⚠️  메시지 커밋 안함 (성공: {success}, 실패: {failed})")
                # 실패 메시지는 커밋하지 않아 다음 재처리 시 다시 처리됨
            
            processed += 1
    
    except KeyboardInterrupt:
        log.info("\n⚠️  사용자에 의해 중단됨")
    
    finally:
        log.info(f"\n📊 DLQ 재처리 완료 통계:")
        log.info(f"  - 처리된 메시지: {processed}개")
        log.info(f"  - 성공: {success}개")
        log.info(f"  - 실패: {failed}개")
        consumer.close()
        connection_pool.closeall()
        producer.flush(5)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DLQ 메시지 재처리')
    parser.add_argument('--group-id', help='Kafka Consumer Group ID')
    parser.add_argument('--max-messages', type=int, help='최대 처리 메시지 수')
    args = parser.parse_args()
    
    main(group_id=args.group_id, max_messages=args.max_messages)
