# 🔄 Kafka Consumer - Flink Stream 처리

Kafka로 수신된 뉴스 데이터를 PostgreSQL, Elasticsearch, HDFS에 순차적으로 저장하는 실시간 Consumer 처리 흐름입니다.

---

## ✅ 주요 흐름

1. Kafka에서 뉴스 데이터를 수신 (`news-topic`)
2. 뉴스 본문 전처리 (내용 정제, 기자명 추출, 키워드/카테고리 분류, 임베딩 생성)
3. PostgreSQL DB에 기사 저장 (중복 URL 무시)
4. Elasticsearch 색인 생성 (검색 가능성 확보)
5. HDFS에 JSON 파일 저장 (날짜별 디렉토리)

---

## 🛠 사용 기술 스택

- **Apache Flink (PyFlink)**: 스트리밍 데이터 처리
- **Kafka**: 뉴스 데이터 소비
- **PostgreSQL**: 정형 데이터 저장
- **Elasticsearch**: 뉴스 검색 색인
- **HDFS**: 장기 보관용 JSON 데이터 저장
- **LangChain / OpenAI** 기반 전처리 (`Preprocess` 클래스)

---

## 🔁 처리 로직 상세

### PgThenEs (MapFunction)

- `title`, `content`, `url`, `write_date` 등의 필드를 파싱
- `Preprocess` 클래스로 전처리 수행:
  - 본문 정제
  - 기자명 추출 (ex. `홍길동 기자`)
  - 키워드 추출 (`extract_keywords`)
  - 카테고리 분류 (`classify_category`)
  - 임베딩 생성 (`transform_to_embedding`)
- **중복 URL**은 PostgreSQL에서 무시
- Elasticsearch 색인 문서 생성 및 URL 기반 doc_id 설정
- HDFS에는 날짜 기준 디렉토리로 JSON 저장

---

## 📂 HDFS 저장 경로 예시
/user/hadoop/news/2025/05/27/news_153245_812374.json


---

## ⚠️ 예외 처리

- PG 중복 URL → 삽입 안 됨 (로그 출력)
- ES 오류 → 상태 코드 및 응답 로그
- HDFS 저장 실패 → 오류 로그 출력 후 계속 진행

---

## ✅ 실행 방법 (Flink job)

```bash
python consumer/flink_job.py
```

## 이 스크립트는 Flink Python 환경에서 실행되며, 실행 전 다음 환경이 구성되어 있어야 합니다:

- Kafka 실행 중

- PostgreSQL DB 연결 가능

- Elasticsearch 실행 중 (localhost:9200)

- HDFS Web UI 및 파일 시스템 동작 (localhost:9870)

---

## 📈 발전 방향

- ✅ 성능 향상: 병렬 처리 및 배치 크기 조절

- ✅ 정합성 강화: PG/ES 성공 여부에 따라 Kafka ack 연동

- ✅ 전처리 다양화: 뉴스 요약 추가, 개체명 인식 등 NLP 확장

- ✅ 모니터링: 처리 건수, 에러율, 처리 시간 등 지표 수집 및 시각화 (Prometheus + Grafana)

- ✅ 이중 전송 방지: URL 기반 Redis 캐시 추가로 필터링 속도 향상