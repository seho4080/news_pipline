# 🗓️ Batch - Airflow DAG 기반 뉴스 리포트 생성

`batch` 디렉토리는 Apache Airflow DAG를 통해 매일 자동으로 실행되는 뉴스 리포트 작업을 정의합니다. Spark를 통해 집계/분석 작업을 수행하며, HDFS에 저장된 뉴스를 기반으로 리포트를 생성합니다.

또한, Elasticsearch와 PostgreSQL 간 데이터 정합성을 평가하는 스크립트를 포함하여, 전송/저장된 데이터의 신뢰성을 점검할 수 있도록 설계되어 있습니다.

---

## ✅ 주요 역할

- 매일 정해진 시간에 실행되는 **Airflow DAG 등록**
- Spark job을 통해 HDFS에 저장된 뉴스 데이터를 분석
- 뉴스 카테고리, 키워드, 작성일 기준 통계 생성
- 생성된 리포트를 다시 HDFS 또는 PostgreSQL에 저장 가능
- **Elasticsearch vs PostgreSQL 정합성 검증 스크립트 제공**

---

## ⚙️ 구성 요소

- `spark_daily_report.py`: 주요 DAG 스크립트로, 매일 Spark job을 실행
- `spark_job/daily_report.py`: Spark로 리포트를 생성하는 PySpark 스크립트
- `scripts/`: HDFS 경로 생성, 파일 이동, 날짜별 관리 유틸 스크립트 포함
- `scripts/data_integrity_check.py`: Elasticsearch와 PostgreSQL 간 기사 개수 및 키 필드 비교를 통해 정합성 평가

---

## 🔁 처리 흐름

1. Airflow 스케줄러가 매일 DAG를 트리거함
2. Spark job이 로컬에서 뉴스 데이터를 불러옴
3. 카테고리/키워드/날짜별 기사 수, 평균 길이 등 통계 생성
4. 결과는 PDF 형식으로 저장
---

1. 정합성 체크 스크립트를 통해 PostgreSQL ↔ Elasticsearch 비교 수행


---

## ✅ 실행 방식

Airflow docker 실행:

```bash
docker compose up -d
```
localhost:8080 로 접속 후 spark 연결 후 DAG실행

---

## 🛠 요구 환경

- Apache Airflow 2.10.5
- Apache Spark 3.5.4
- Elasticsearch 및 PostgreSQL 서버 실행 중
- Docker 기반 실행

---

## 📈 발전 방향

- ✅ 뉴스 키워드, 카테고리별 트렌드 분석 리포트 생성
- ✅ Slack으로 리포트 자동 전송
- ✅ DAG 성공/실패 여부에 대한 모니터링 및 알림 연동
- ✅ Airflow + Spark + Grafana 연동으로 리포트 시각화 자동화
- ✅ 정합성 체크 결과를 리포트 형태로 로그 및 DB에 저장
- ✅ 다양한 소스의 뉴스 데이터 수집으로 폭 넓은 분석 제공
> ⏱️ 정기적인 배치 처리를 통해 뉴스 추천 품질을 높이고, 사용자 행동 기반 리포트까지 확장 가능합니다.
