# ⚙️ Batch Processing 가이드

Apache Airflow + Spark를 활용한 배치 데이터 처리 완벽 가이드입니다.

---

## 🏗️ 배치 시스템 아키텍처

### 역할
```
┌────────────────────────────────────────┐
│  Batch Processing (Scheduled Jobs)    │
├────────────────────────────────────────┤
│ • 일일 뉴스 리포트 생성                 │
│ • 통계 계산 (카테고리별, 감정별)         │
│ • Elasticsearch ↔ PostgreSQL 동기화    │
│ • 데이터 정제 & 집계                   │
│ • 아카이빙 & 백업                      │
└────────────────────────────────────────┘
        ↓                         ↓
   Airflow             Spark (분산 처리)
  (스케줄)            (병렬 처리)
```

### 기술 스택
- **Airflow:** 워크플로우 오케스트레이션
- **Spark:** 대용량 데이터 처리
- **PostgreSQL:** 데이터 저장소
- **Elasticsearch:** 검색 인덱스

---

## 📁 디렉토리 구조

```
batch/
├── docker-compose.yaml        # Airflow + Spark 환경
├── Dockerfile.airflow         # Airflow 컨테이너
├── Dockerfile.spark           # Spark 컨테이너
├── setup.sh                   # 초기 설정 스크립트
│
├── dags/                      # Airflow DAG 정의
│   ├── daily_report_dag.py    # 일일 리포트 생성
│   ├── spark_daily_report_dag.py  # Spark 기반 리포트
│   ├── psql_es_synchronization.py # DB-ES 동기화
│   └── scripts/               # 헬퍼 스크립트
│       ├── generate_report.py
│       └── sync_elasticsearch.py
│
├── data/                      # 데이터 디렉토리
│   ├── daily_report/          # 생성된 리포트
│   └── news_archive/          # 뉴스 아카이브
│
├── output/                    # 처리 결과
│   ├── _SUCCESS
│   └── part-*.csv            # Spark 출력
│
├── logs/                      # 로그
│   └── scheduler/
│
└── plugins/                   # 커스텀 플러그인
    └── shell/
```

---

## 🚀 빠른 시작

### 1단계: 환경 설정

```bash
cd batch

# Docker 이미지 빌드
docker-compose build

# 서비스 시작
docker-compose up -d

# Airflow 웹 UI 접속
http://localhost:8080
# 기본 로그인: admin / admin
```

### 2단계: Airflow 설정

```bash
# 1. PostgreSQL 연결 설정
# Airflow UI → Admin → Connections → 새로 추가
# Connection Id: postgres_default
# Connection Type: Postgres
# Host: postgres
# Database: airflow
# Login: airflow
# Password: airflow_password

# 2. Spark 연결 설정
# Connection Id: spark_default
# Connection Type: Spark
# Host: spark-master
# Port: 7077
```

### 3단계: DAG 활성화

```bash
# Airflow UI에서 DAG 활성화
# - daily_report_dag
# - spark_daily_report_dag
# - psql_es_synchronization
```

---

## 📊 DAG (Directed Acyclic Graph) 상세

### 1. 일일 리포트 DAG (daily_report_dag.py)

**일정:** 매일 자정 (00:00 UTC)

```python
# dags/daily_report_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'news-team',
    'start_date': datetime(2024, 1, 1),
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'daily_report_dag',
    default_args=default_args,
    description='Generate daily news report',
    schedule_interval='0 0 * * *',  # 매일 00:00
    catchup=False,
)

# Task 1: 데이터 추출
def extract_daily_data(**context):
    """
    어제 발행된 모든 기사 추출
    """
    import psycopg2
    from datetime import datetime, timedelta
    
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    conn = psycopg2.connect(
        host='postgres',
        database='newsdb',
        user='newsuser',
        password='news_password'
    )
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, url, title, content, category, sentiment
        FROM mynews_article
        WHERE DATE(published_at) = %s
        ORDER BY published_at DESC
    """, (yesterday,))
    
    articles = cursor.fetchall()
    conn.close()
    
    context['task_instance'].xcom_push(key='articles', value=articles)
    print(f"✓ Extracted {len(articles)} articles from {yesterday}")

# Task 2: 통계 계산
def calculate_statistics(**context):
    """
    카테고리별, 감정별 통계 계산
    """
    articles = context['task_instance'].xcom_pull(
        task_ids='extract_daily_data',
        key='articles'
    )
    
    stats = {
        'total_articles': len(articles),
        'by_category': {},
        'by_sentiment': {},
    }
    
    for article in articles:
        category = article[4]
        sentiment = article[5]
        
        # 카테고리별 집계
        if category not in stats['by_category']:
            stats['by_category'][category] = 0
        stats['by_category'][category] += 1
        
        # 감정별 집계
        if sentiment not in stats['by_sentiment']:
            stats['by_sentiment'][sentiment] = 0
        stats['by_sentiment'][sentiment] += 1
    
    context['task_instance'].xcom_push(key='statistics', value=stats)
    print(f"✓ Calculated statistics: {stats}")

# Task 3: 리포트 생성
def generate_report(**context):
    """
    통계를 기반으로 리포트 생성 (CSV, JSON)
    """
    import json
    from datetime import datetime, timedelta
    
    articles = context['task_instance'].xcom_pull(
        task_ids='extract_daily_data',
        key='articles'
    )
    stats = context['task_instance'].xcom_pull(
        task_ids='calculate_statistics',
        key='statistics'
    )
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # JSON 리포트
    report_data = {
        'date': yesterday,
        'statistics': stats,
        'articles': {
            'total': len(articles),
            'sample': [
                {
                    'id': a[0],
                    'title': a[2],
                    'category': a[4],
                    'sentiment': a[5]
                } for a in articles[:10]
            ]
        }
    }
    
    report_path = f'/data/daily_report/{yesterday}_report.json'
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Report generated: {report_path}")

# Task 4: 데이터베이스에 저장
def save_to_database(**context):
    """
    통계를 데이터베이스 statistics 테이블에 저장
    """
    import psycopg2
    from datetime import datetime, timedelta
    
    stats = context['task_instance'].xcom_pull(
        task_ids='calculate_statistics',
        key='statistics'
    )
    
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    conn = psycopg2.connect(
        host='postgres',
        database='newsdb',
        user='newsuser',
        password='news_password'
    )
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO statistics (date, data)
        VALUES (%s, %s)
        ON CONFLICT (date) DO UPDATE
        SET data = %s, updated_at = NOW()
    """, (yesterday, stats, stats))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Statistics saved to database")

# DAG 정의
task_extract = PythonOperator(
    task_id='extract_daily_data',
    python_callable=extract_daily_data,
    dag=dag,
)

task_stats = PythonOperator(
    task_id='calculate_statistics',
    python_callable=calculate_statistics,
    dag=dag,
)

task_report = PythonOperator(
    task_id='generate_report',
    python_callable=generate_report,
    dag=dag,
)

task_save = PythonOperator(
    task_id='save_to_database',
    python_callable=save_to_database,
    dag=dag,
)

# 의존성 설정
task_extract >> task_stats >> [task_report, task_save]
```

### 2. Spark 기반 고성능 DAG (spark_daily_report_dag.py)

**일정:** 매일 01:00 UTC (대용량 데이터용)

```python
# dags/spark_daily_report_dag.py
from airflow import DAG
from airflow.operators.spark_submit_operator import SparkSubmitOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'news-team',
    'start_date': datetime(2024, 1, 1),
    'retries': 2,
}

dag = DAG(
    'spark_daily_report_dag',
    default_args=default_args,
    description='Generate report using Spark',
    schedule_interval='0 1 * * *',  # 매일 01:00
    catchup=False,
)

# Spark 작업
spark_job = SparkSubmitOperator(
    task_id='spark_news_analysis',
    application='/dags/scripts/spark_analysis.py',
    conf={
        'spark.executor.memory': '2g',
        'spark.executor.cores': '2',
        'spark.driver.memory': '2g',
    },
    spark_home='/opt/spark',
    master='spark://spark-master:7077',
    deploy_mode='cluster',
    dag=dag,
)
```

```python
# dags/scripts/spark_analysis.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import count, col, groupBy
from datetime import datetime, timedelta

spark = SparkSession.builder \
    .appName("NewsAnalysis") \
    .config("spark.postgresql.host", "postgres") \
    .getOrCreate()

# PostgreSQL에서 데이터 읽기
articles = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:postgresql://postgres:5432/newsdb") \
    .option("dbtable", "mynews_article") \
    .option("user", "newsuser") \
    .option("password", "news_password") \
    .load()

yesterday = (datetime.now() - timedelta(days=1)).date()

# 어제 데이터 필터링
filtered = articles.filter(
    col("published_at").cast("date") == yesterday
)

# 카테고리별 분석
category_stats = filtered.groupBy("category").agg(
    count("*").alias("count"),
    avg("sentiment_score").alias("avg_sentiment")
).collect()

# 감정별 분석
sentiment_stats = filtered.groupBy("sentiment").agg(
    count("*").alias("count")
).collect()

# CSV로 저장
filtered.write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(f"/output/{yesterday}_articles")

print(f"✓ Spark analysis completed for {yesterday}")
```

### 3. 동기화 DAG (psql_es_synchronization.py)

**일정:** 매일 02:00 UTC (DB-ES 동기화)

```python
# dags/psql_es_synchronization.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'news-team',
    'start_date': datetime(2024, 1, 1),
}

dag = DAG(
    'psql_es_synchronization',
    default_args=default_args,
    description='Synchronize PostgreSQL to Elasticsearch',
    schedule_interval='0 2 * * *',  # 매일 02:00
    catchup=False,
)

def sync_elasticsearch(**context):
    """
    PostgreSQL의 기사 데이터를 Elasticsearch로 동기화
    """
    import psycopg2
    from elasticsearch import Elasticsearch
    from datetime import datetime, timedelta
    
    # PostgreSQL 연결
    pg_conn = psycopg2.connect(
        host='postgres',
        database='newsdb',
        user='newsuser',
        password='news_password'
    )
    
    # Elasticsearch 연결
    es = Elasticsearch(['http://elasticsearch:9200'])
    
    cursor = pg_conn.cursor()
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    # 어제 추가된 기사 조회
    cursor.execute("""
        SELECT id, url, title, content, category, sentiment, published_at
        FROM mynews_article
        WHERE DATE(created_at) = %s
    """, (yesterday,))
    
    articles = cursor.fetchall()
    pg_conn.close()
    
    # Elasticsearch로 인덱싱
    count = 0
    for article in articles:
        doc = {
            'id': article[0],
            'url': article[1],
            'title': article[2],
            'content': article[3],
            'category': article[4],
            'sentiment': article[5],
            'published_at': article[6].isoformat(),
            'synced_at': datetime.now().isoformat()
        }
        
        # URL을 기반으로 upsert
        es.index(
            index='news-prod',
            id=article[0],
            body=doc
        )
        count += 1
    
    print(f"✓ Synchronized {count} articles to Elasticsearch")

sync_task = PythonOperator(
    task_id='sync_to_elasticsearch',
    python_callable=sync_elasticsearch,
    dag=dag,
)
```

---

## 🎛️ Airflow UI 사용법

### 1. DAG 모니터링

```
Airflow UI → DAGs 탭
├── DAG 이름 클릭
├── Graph View: 작업 흐름 시각화
├── Tree View: 실행 히스토리
└── Calendar View: 일정별 실행 상태
```

### 2. 수동 실행

```bash
# CLI에서 DAG 수동 실행
docker-compose exec airflow-scheduler \
  airflow dags trigger daily_report_dag

# 특정 날짜로 실행
docker-compose exec airflow-scheduler \
  airflow dags backfill \
  --start-date 2024-01-01 \
  --end-date 2024-01-10 \
  daily_report_dag
```

### 3. 로그 확인

```bash
# Task 로그 보기
docker-compose logs -f airflow-scheduler

# 특정 DAG 로그
docker-compose exec airflow-scheduler \
  airflow tasks logs daily_report_dag \
  extract_daily_data 2024-01-01
```

---

## ⚙️ 성능 최적화

### 1. 병렬 처리

```python
# DAG 설정에서 병렬 작업 수
dag = DAG(
    'daily_report_dag',
    max_active_runs=2,  # 동시 실행 제한
)

# Task 레벨
task1 >> task2  # 순차 실행
[task1, task2, task3] >> task4  # 병렬 실행 후 task4
```

### 2. Spark 최적화

```python
SparkSubmitOperator(
    conf={
        'spark.executor.memory': '4g',      # 메모리 증가
        'spark.executor.cores': '4',        # 코어 증가
        'spark.driver.memory': '2g',
        'spark.dynamicAllocation.enabled': 'true',  # 동적 할당
        'spark.dynamicAllocation.minExecutors': '2',
        'spark.dynamicAllocation.maxExecutors': '10',
    }
)
```

### 3. 데이터 분할

```python
# Spark의 파티셔닝
articles.repartition(10) \  # 10개 파티션으로 분할
    .write \
    .mode("overwrite") \
    .parquet(output_path)
```

---

## 🔍 모니터링 & 알람

### 1. Airflow 알람 설정

```python
def on_failure_callback(context):
    """
    작업 실패 시 콜백
    """
    task = context['task']
    exception = context['exception']
    
    # 슬랙 알림
    send_slack_message(
        channel='#alerts',
        message=f"❌ Task failed: {task.task_id}\n{exception}"
    )

default_args = {
    'on_failure_callback': on_failure_callback,
}
```

### 2. 성공/실패 추적

```python
# XCom을 통한 상태 전달
context['task_instance'].xcom_push(
    key='status',
    value='success'
)

# 다음 작업에서 확인
status = context['task_instance'].xcom_pull(
    task_ids='previous_task',
    key='status'
)

if status != 'success':
    raise Exception("Previous task failed")
```

---

## 📊 리포트 예시

### 생성되는 일일 리포트 (JSON)

```json
{
  "date": "2024-01-01",
  "statistics": {
    "total_articles": 150,
    "by_category": {
      "기술": 45,
      "과학": 35,
      "비즈니스": 40,
      "엔터테인먼트": 30
    },
    "by_sentiment": {
      "positive": 60,
      "neutral": 70,
      "negative": 20
    }
  },
  "articles": {
    "total": 150,
    "sample": [
      {
        "id": 1,
        "title": "Breaking Tech News",
        "category": "기술",
        "sentiment": "positive"
      }
    ]
  }
}
```

---

## 🆘 트러블슈팅

### 1. Airflow가 DAG을 감지하지 못함

```bash
# 1. DAG 파일 확인
ls -la dags/

# 2. 파일 권한 확인
chmod 644 dags/daily_report_dag.py

# 3. Python 문법 확인
python -m py_compile dags/daily_report_dag.py

# 4. Airflow 재시작
docker-compose restart airflow-scheduler
```

### 2. Task 실패

```bash
# 로그 확인
docker-compose logs airflow-scheduler | grep ERROR

# Task 재실행
airflow tasks clear daily_report_dag -t extract_daily_data -d

# 전체 DAG 재시작
airflow dags backfill -s 2024-01-01 -e 2024-01-01 daily_report_dag
```

### 3. Spark 작업 느림

```python
# Spark UI에서 확인: http://localhost:4040

# 최적화:
# 1. 파티션 수 증가
# 2. 메모리 할당 증가
# 3. 데이터 필터링 추가 (WHERE 절)
# 4. 불필요한 컬럼 제거 (SELECT 절)
```

---

## 📚 추가 리소스

- Apache Airflow: https://airflow.apache.org/
- Apache Spark: https://spark.apache.org/
- Airflow Tutorials: https://airflow.apache.org/docs/

---

**마지막 업데이트:** 2026-01-02  
**버전:** 1.0  
**상태:** ✅ 프로덕션 준비 완료
