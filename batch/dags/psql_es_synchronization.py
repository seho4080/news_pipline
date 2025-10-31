from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import psycopg2, json
from urllib.parse import quote  # Elasticsearch 문서 ID로 URL 안전하게 인코딩하기 위함
from dotenv import load_dotenv
from airflow.utils.log.logging_mixin import LoggingMixin
# 나중에 .env 파일 경로 설정해야함
# load_dotenv(dotenv_path=Path("/opt/airflow/.env"))

    # conn = psycopg2.connect(
    #     host=os.getenv("DB_HOST"),
    #     database=os.getenv("DB_NAME"),
    #     user=os.getenv("DB_USERNAME"),
    #     password=os.getenv("DB_PASSWORD")
    # )

# DAG 기본 설정
default_args = {
    "owner": "airflow",  # DAG 소유자
    "start_date": datetime(2024, 1, 1),  # DAG 시작 날짜
    "retries": 1,  # 실패 시 재시도 횟수
    "retry_delay": timedelta(minutes=5),  # 재시도 간격
}
logger = LoggingMixin().log

# PostgreSQL → Elasticsearch 동기화 함수
def sync_to_es():
    conn = None
    cursor = None
    
    try:
        # PostgreSQL 연결 (환경 변수 사용 권장)
        import os
        db_host = os.getenv("DB_HOST", "host.docker.internal")
        db_name = os.getenv("DB_NAME", "news")
        db_user = os.getenv("DB_USER", "ssafyuser")
        db_pass = os.getenv("DB_PASSWORD", "ssafy")
        
        logger.info(f"🔗 PostgreSQL 연결 시도: {db_host}/{db_name}")
        
        conn = psycopg2.connect(
            host=db_host,
            database=db_name, 
            user=db_user, 
            password=db_pass,
            connect_timeout=10
        )
        
        cursor = conn.cursor()

        # 최근 5분 내 변경된 뉴스 데이터 조회
        cursor.execute("""
            SELECT title, writer, write_date, category, content, url, keywords, updated_at
            FROM news_article
            WHERE updated_at > now() - interval '5 minutes'
        """)
        rows = cursor.fetchall()
        
        if not rows:
            logger.info("🔍 변경된 뉴스 기사가 없음 (5분 내).")
            return
        else:
            logger.info(f"📰 {len(rows)}개 문서 처리 시작")

        # Elasticsearch 클라이언트 생성 (환경 변수 사용 권장)
        es_host = os.getenv("ES_HOST", "http://elasticsearch:9200")
        logger.info(f"🔍 Elasticsearch 연결 시도: {es_host}")
        
        es = Elasticsearch(es_host, request_timeout=30)
        
        # 연결 확인
        if not es.ping():
            logger.error("❌ Elasticsearch 연결 실패")
            return
        
        count = 0
        error_count = 0
        
        for row in rows:
            try:
                # URL을 안전하게 인코딩하여 ES 문서 ID로 사용
                doc_id = quote(row[5], safe='')

                # 문서 구조 정의
                doc = {
                    "title": row[0],
                    "writer": row[1],
                    "write_date": row[2].isoformat() if row[2] else None,
                    "category": row[3],
                    "content": row[4],
                    "url": row[5],
                    "keywords": row[6],
                    "updated_at": row[7].isoformat() if row[7] else None
                }

                # Elasticsearch에 문서 저장
                if not es.exists(index="news", id=doc_id):
                    es.index(index="news", id=doc_id, document=doc)
                    count += 1
                    logger.info(f"✅ 저장 완료: {doc_id}")
                else:
                    logger.debug(f"⏭️ 이미 존재: {doc_id}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"❌ 문서 색인 실패: {row[5] if len(row) > 5 else 'unknown'} - {e}")
        
        logger.info(f"✅ 동기화 완료: {count}개 성공, {error_count}개 실패")
        
    except psycopg2.OperationalError as e:
        logger.error(f"❌ PostgreSQL 연결 실패: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ 동기화 프로세스 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        # 리소스 정리
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.info("🔌 DB 연결 종료")

# DAG 정의
with DAG(
    dag_id="sync_pg_to_es",  # DAG 이름
    default_args=default_args,  # 기본 인자
    schedule_interval="*/5 * * * *",  # 매 5분마다 실행 (cron 형식)
    catchup=False,  # 이전 실행 누락분 실행 안 함
) as dag:
    # Python 함수 task 정의
    sync_task = PythonOperator(
        task_id="sync_postgres_to_elasticsearch",  # task 이름
        python_callable=sync_to_es,  # 실행할 함수
    )

