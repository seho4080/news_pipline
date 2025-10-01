# 🗓️ Batch - Airflow DAG 기반 뉴스 리포트 생성

`batch` 디렉토리는 Apache Airflow DAG를 통해 매일 자동으로 실행되는 뉴스 리포트 작업을 정의합니다. Spark를 통해 집계/분석 작업을 수행하며, HDFS에 저장된 뉴스를 기반으로 리포트를 생성합니다.

---

## ✅ 주요 역할

- 매일 정해진 시간에 실행되는 **Airflow DAG 등록**
- Spark job을 통해 HDFS에 저장된 뉴스 데이터를 분석
- 뉴스 카테고리, 키워드, 작성일 기준 통계 생성
- 생성된 리포트를 다시 HDFS 또는 PostgreSQL에 저장 가능

---

## ⚙️ 구성 요소

- `dags/spark_daily_report.py`: 주요 DAG 스크립트로, 매일 Spark job을 실행
- `spark_job/daily_report.py`: Spark로 리포트를 생성하는 PySpark 스크립트
- `scripts/`: HDFS 경로 생성, 파일 이동, 날짜별 관리 유틸 스크립트 포함

---

## 🔁 처리 흐름

1. Airflow 스케줄러가 매일 DAG를 트리거함
2. Spark job이 HDFS에서 뉴스 데이터를 불러옴
3. 카테고리/키워드/날짜별 기사 수, 평균 길이 등 통계 생성
4. 결과는 JSON 또는 CSV 형식으로 저장
5. 추후 대시보드, 보고서 등에 활용 가능

---

## ✅ 실행 방식

Airflow 웹 UI 또는 CLI에서 다음 DAG를 수동/자동 실행:

```bash
airflow dags trigger spark_daily_report
```

> Spark job은 `spark-submit`을 통해 실행되며, Docker 또는 로컬 환경에 Spark가 구성되어 있어야 합니다.

---

## 🛠 요구 환경

- Apache Airflow 2.x (CeleryExecutor 추천)
- Apache Spark 3.x (로컬 또는 YARN 모드)
- HDFS 클러스터 또는 단일 노드 (NameNode + DataNode)
- Docker 기반 실행 권장 (Docker Compose로 구성 시 편리함)

---

## 📈 발전 방향

- ✅ Spark 처리 결과를 PostgreSQL 테이블로 저장 → 대시보드와 연동
- ✅ 뉴스 키워드, 카테고리별 트렌드 분석 리포트 생성
- ✅ Slack, 이메일 등으로 리포트 자동 전송
- ✅ DAG 성공/실패 여부에 대한 모니터링 및 알림 연동
- ✅ Airflow + Spark + Grafana 연동으로 리포트 시각화 자동화

> ⏱️ 정기적인 배치 처리를 통해 뉴스 추천 품질을 높이고, 사용자 행동 기반 리포트까지 확장 가능합니다.
