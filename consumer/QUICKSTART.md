# 🔄 Kafka Consumer - 실행 가이드

## 📝 개요

이 Consumer는 Kafka `news-topic`에서 뉴스 메시지를 수신하여 전처리한 후:
- **PostgreSQL** 에 정형 데이터 저장
- **Elasticsearch** 에 전문 검색 인덱싱
- **DLQ (Dead Letter Queue)** 로 실패 메시지 전송

---

## 🚀 빠른 시작

### 1. 환경 설정

**.env 파일 생성:**
```bash
cp .env.example .env
```

**.env 내용:**
```env
# Kafka
KAFKA_BOOTSTRAP=kafka:9092
IN_TOPIC=news-topic
DLQ_TOPIC=news-dlq
GROUP_ID=python-news-group

# PostgreSQL
DB_HOST=postgres
DB_NAME=news_db
DB_USERNAME=postgres
DB_PASSWORD=postgres
DB_MIN_CONN=1
DB_MAX_CONN=5
DB_TIMEOUT=10
DB_IDLE_TIMEOUT=600

# Elasticsearch
ES_BASE_URL=http://elasticsearch:9200
ES_INDEX=news
ES_TIMEOUT=10

# 로깅
LOG_LEVEL=INFO
LOG_DIR=/app/logs

# pgvector 사용 여부 (임베딩 저장)
USE_PGVECTOR=false
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 실행

**기본 실행:**
```bash
python news_preprocessor.py
```

**DEBUG 로깅 활성화:**
```bash
LOG_LEVEL=DEBUG python news_preprocessor.py
```

**Docker에서 실행:**
```bash
docker-compose up consumer
```

---

## 📊 모니터링 & 로깅

### 실시간 로그 확인

```bash
# 전체 로그
tail -f logs/consumer_stats.csv

# INFO 레벨만 (에러 및 주요 정보)
grep "INFO" logs/*.log

# DEBUG 레벨 (상세 로깅)
grep "DEBUG" logs/*.log
```

### 통계 CSV 파일

**위치:** `logs/consumer_stats.csv`

**컬럼:**
- 종료시각: 통계 저장 시점
- 실행시간(초): 누적 실행 시간
- 소비_메시지: 수신한 메시지 수
- 전처리_성공: 성공적으로 전처리된 메시지
- DB_성공/DB_실패: PostgreSQL 저장 결과
- DB_성공률(%): DB 성공 비율
- ES_성공/ES_실패: Elasticsearch 색인 결과
- ES_성공률(%): ES 성공 비율
- JSON_디코드_실패: JSON 파싱 실패
- 전처리_실패: AI 모델 전처리 실패
- 카테고리별_상세: 카테고리별 처리 현황 (JSON)

---

## 🔧 주요 기능

### 1. 자동 재시도 (Exponential Backoff)

**PostgreSQL 실패 시:**
- 최대 3회 재시도
- 대기 시간: 2초 → 4초 → 8초
- 최종 실패 시 DLQ 전송

**Elasticsearch 실패 시:**
- 최대 3회 재시도 (DB와 동일)
- 최종 실패 시 DLQ 전송

### 2. DLQ (Dead Letter Queue) 처리

**실패 메시지 구성:**
```json
{
  "reason": "es_upsert_failed|db_insert_failed|preprocess_error",
  "row": { 원본 데이터 },
  "error": "에러 메시지"
}
```

**DLQ 재처리:**
```bash
# 기본 (무한 재처리)
python dlq_reprocessor.py

# 최대 100개만 처리
python dlq_reprocessor.py --max-messages 100

# 특정 그룹으로 처리
python dlq_reprocessor.py --group-id my-dlq-group
```

### 3. 안전한 종료 (Graceful Shutdown)

**신호 처리:**
```bash
# SIGTERM 수신 시
kill -TERM <PID>

# SIGINT (Ctrl+C)
Ctrl+C
```

**동작:**
1. 현재 메시지 처리 완료
2. 최종 통계 저장
3. 모든 리소스 정리
4. 안전한 종료

### 4. 에러 샘플링 로깅

**같은 에러 반복 방지:**
- 처음 10회: 전체 로깅
- 이후: 100번마다 1회 로깅

**목적:** 로그 파일 과다 증가 방지

### 5. 주기적 가비지 컬렉션

- 5개 메시지마다 자동 GC 실행
- 메모리 누수 방지

---

## ⚙️ 환경변수 상세

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `KAFKA_BOOTSTRAP` | localhost:9092 | Kafka 브로커 주소 |
| `IN_TOPIC` | news-topic | 입력 토픽명 |
| `DLQ_TOPIC` | news-dlq | DLQ 토픽명 |
| `GROUP_ID` | python-news-group | Consumer 그룹 |
| `DB_HOST` | - | PostgreSQL 호스트 (필수) |
| `DB_NAME` | - | 데이터베이스명 (필수) |
| `DB_USERNAME` | - | DB 사용자명 (필수) |
| `DB_PASSWORD` | - | DB 비밀번호 (필수) |
| `DB_MIN_CONN` | 1 | 최소 연결 풀 |
| `DB_MAX_CONN` | 5 | 최대 연결 풀 |
| `DB_TIMEOUT` | 10 | DB 연결 타임아웃 (초) |
| `DB_IDLE_TIMEOUT` | 600 | 유휴 연결 종료 시간 (초) |
| `ES_BASE_URL` | http://localhost:9200 | Elasticsearch URL |
| `ES_INDEX` | news | ES 인덱스명 |
| `ES_TIMEOUT` | 10 | ES 타임아웃 (초) |
| `LOG_LEVEL` | INFO | 로깅 레벨 (DEBUG/INFO/WARNING/ERROR) |
| `LOG_DIR` | /app/logs | 로그 디렉토리 |
| `USE_PGVECTOR` | false | pgvector 사용 여부 |

---

## 🔍 문제 해결

### 1. DB 연결 실패

```
❌ DB 연결 풀 생성 실패: could not connect to server
```

**해결:**
```bash
# PostgreSQL 상태 확인
docker ps | grep postgres

# 연결 테스트
psql -h postgres -U postgres -d news_db -c "SELECT 1"

# 환경변수 확인
echo $DB_HOST $DB_NAME $DB_USERNAME
```

### 2. Elasticsearch 연결 실패

```
❌ ES upsert failed: 503 Service Unavailable
```

**해결:**
```bash
# ES 상태 확인
curl -s http://elasticsearch:9200/_cluster/health | jq

# ES 인덱스 생성
curl -X PUT "http://elasticsearch:9200/news"
```

### 3. Kafka 메시지 없음

```
로그에 처리 메시지가 없음
```

**해결:**
```bash
# 토픽 존재 여부 확인
kafka-topics.sh --list --bootstrap-server kafka:9092

# 토픽 생성
kafka-topics.sh --create --topic news-topic --bootstrap-server kafka:9092

# 메시지 전송 테스트
kafka-console-producer.sh --broker-list kafka:9092 --topic news-topic
```

### 4. 메모리 누수

```
❌ MemoryError
```

**해결:**
```bash
# GC 임계값 감소 (기본값: 5개마다 GC)
# news_preprocessor.py의 SAVE_INTERVAL 값 감소

# 또는 Python 메모리 제한
PYTHONUNBUFFERED=1 python -u news_preprocessor.py
```

---

## 📈 성능 튜닝

### 1. 동시성 증가

```bash
# Consumer 인스턴스 여러 개 실행
GROUP_ID=news-consumer-1 python news_preprocessor.py &
GROUP_ID=news-consumer-2 python news_preprocessor.py &
GROUP_ID=news-consumer-3 python news_preprocessor.py &
```

### 2. Kafka 파티션 증가

```bash
# 파티션 3개로 증가
kafka-topics.sh --alter --topic news-topic --partitions 3 --bootstrap-server kafka:9092
```

### 3. DB 연결 풀 최적화

```bash
# .env에서
DB_MIN_CONN=3
DB_MAX_CONN=10
```

### 4. 배치 처리 고려

현재는 메시지 단위 처리입니다. 성능 향상을 원하면 배치 처리로 변경 가능합니다.

---

## 🎓 아키텍처

```
┌─────────────┐
│Kafka Topic  │
│ news-topic  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Kafka Consumer (news_preprocessor) │
│  ✅ 재시도 + DLQ + Graceful Shutdown │
└──────┬────────────────┬──────────────┘
       │                │
       ▼                ▼
  PostgreSQL      Elasticsearch
  ✅ Upsert       ✅ Upsert
  ✅ URL 멱등키    ✅ URL 멱등키
       │                │
       └────────┬───────┘
                ▼
         CSV 통계 로그
         (매 5개마다 저장)
         
     ❌ 실패 메시지
          │
          ▼
    Kafka DLQ Topic
    news-dlq
          │
          ▼
   DLQ Reprocessor
   (별도 스크립트)
```

---

## 📞 지원

문제가 발생하면:
1. 로그 파일 확인: `logs/consumer_stats.csv`
2. DEBUG 로깅 활성화: `LOG_LEVEL=DEBUG`
3. 환경변수 확인: `env | grep -E "^(KAFKA|DB|ES)"`
4. 외부 서비스 상태 확인 (Kafka, PostgreSQL, Elasticsearch)

---

**최종 업데이트:** 2026-01-02
