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
    # PostgreSQL 연결
    conn = psycopg2.connect(
        # host="127.0.0.1",
        # host = "172.22.176.175",
        host = "host.docker.internal",
        database="news", 
        user="ssafyuser", 
        password="ssafy"
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
    else:
        logger.info(f"📰 {len(rows)}개 문서 처리 시작")

    # Elasticsearch 클라이언트 생성
    # es = Elasticsearch("http://localhost:9200") -> 로컬 
    # es = Elasticsearch("http://es01:9200") -> 같은 도커내에 있으면 
    es = Elasticsearch("http://172.18.0.5:9200") #-> 내 ip주면서 es호출
    count = 0
    for row in rows:
        # URL을 안전하게 인코딩하여 ES 문서 ID로 사용
        doc_id = quote(row[5], safe='')

        # 문서 구조 정의
        doc = {
            "title": row[0],
            "writer": row[1],
            "write_date": row[2].isoformat(),
            "category": row[3],
            "content": row[4],
            "url": row[5],
            "keywords": row[6],
            "updated_at": row[7].isoformat()
        }

        # Elasticsearch에 문서 저장
            # 존재 여부 확인
        if not es.exists(index="news", id=doc_id):
            # 없으면 저장
            es.index(index="news", id=doc_id, document=doc)
            count += 1
            print("없는 데이터 저장")
        else:
            # 존재하면 무시 (or log)
            print(f"🔁 이미 존재하는 문서: {doc_id}")
            logger.info(f"⚠️ 이미 존재: {doc_id}")
    logger.info(f"✅ {count}개 문서 Elasticsearch에 저장 완료")
    # 리소스 정리
    cursor.close()
    conn.close()

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

