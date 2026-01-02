# 📮 DLQ Reprocessor - Dead Letter Queue 재처리 가이드

## 개요

**DLQ (Dead Letter Queue)** 는 Consumer에서 처리하지 못한 메시지를 보관하는 토픽입니다.
이 스크립트는 DLQ의 메시지를 다시 처리합니다.

---

## 실패 메시지 유형

### 1. Elasticsearch 실패 (es_upsert_failed)

```json
{
  "reason": "es_upsert_failed",
  "row": {
    "title": "뉴스 제목",
    "url": "https://example.com",
    "content": "본문",
    ...
  },
  "error": "ConnectionError: Failed to connect to Elasticsearch"
}
```

**원인:**
- Elasticsearch 서버 다운
- 네트워크 연결 끊김
- 디스크 공간 부족 (413 Payload Too Large)

**해결:**
1. Elasticsearch 상태 확인
2. 서버 재시작 후 재처리
3. 필요시 인덱스 설정 조정

### 2. PostgreSQL 실패 (db_insert_failed)

```json
{
  "reason": "db_insert_failed",
  "row": { ... },
  "error": "psycopg2.OperationalError: could not connect to server"
}
```

**원인:**
- PostgreSQL 서버 다운
- 데이터베이스 용량 초과
- 테이블 제약 조건 위반

**해결:**
1. PostgreSQL 상태 확인
2. 디스크 여유 공간 확보
3. 제약 조건 확인 후 재처리

### 3. 전처리 실패 (preprocess_error)

```json
{
  "reason": "preprocess_error",
  "raw": { 원본 JSON 메시지 },
  "error": "OpenAI API timeout"
}
```

**원인:**
- OpenAI API 타임아웃
- LangChain 모델 로드 실패
- 입력 데이터 형식 오류

**해결:**
1. API 키 확인
2. 네트워크 연결 확인
3. 타임아웃 값 증가

---

## 사용 방법

### 기본 사용

```bash
# 무한 재처리 (Ctrl+C로 중단)
python dlq_reprocessor.py

# 로그 레벨 설정
LOG_LEVEL=DEBUG python dlq_reprocessor.py
```

### 제한된 메시지 처리

```bash
# 최대 100개만 처리
python dlq_reprocessor.py --max-messages 100

# 최대 1000개 처리 (큰 DLQ 대응)
python dlq_reprocessor.py --max-messages 1000
```

### Consumer Group 지정

```bash
# 기본: dlq-reprocessor-<timestamp>
python dlq_reprocessor.py

# 특정 그룹으로 지정 (여러 인스턴스 병렬 처리)
python dlq_reprocessor.py --group-id my-dlq-group-1
python dlq_reprocessor.py --group-id my-dlq-group-2
```

### 결합 사용

```bash
# 특정 그룹으로 최대 500개 처리
python dlq_reprocessor.py --group-id prod-dlq --max-messages 500
```

---

## 모니터링

### 재처리 진행상황 확인

```bash
# 실시간 로그 모니터링
tail -f dlq_reprocessor.log

# 성공/실패 통계 확인
grep "재처리" dlq_reprocessor.log
```

### 결과 분석

```
✅ 메시지 커밋 (성공: 15, 실패: 2)
⚠️  메시지 커밋 안함 (성공: 15, 실패: 3)
```

**의미:**
- `커밋`: Kafka 오프셋 저장 (메시지 처리 완료)
- `커밋 안함`: 오프셋 미저장 (다음 실행에서 다시 처리)

---

## 트러블슈팅

### 1. "Consumer Lag 계속 증가"

```
문제: 재처리 속도 < DLQ 수신 속도
```

**해결:**
```bash
# 여러 인스턴스로 병렬 처리
python dlq_reprocessor.py --group-id dlq-1 &
python dlq_reprocessor.py --group-id dlq-2 &
python dlq_reprocessor.py --group-id dlq-3 &
```

### 2. "계속 같은 메시지만 반복"

```
원인: 외부 서비스가 계속 실패 중
```

**해결:**
```bash
# 최대 메시지 제한으로 처리 중단
python dlq_reprocessor.py --max-messages 50

# 외부 서비스 상태 확인 후 재실행
curl http://elasticsearch:9200/_cluster/health
psql -h postgres -U postgres -d news_db -c "SELECT 1"
```

### 3. "메모리 사용량 증가"

```
원인: 대용량 메시지 누적
```

**해결:**
```bash
# 배치 처리 크기 감소
python dlq_reprocessor.py --max-messages 10

# 정기적으로 재시작
# (cron 또는 systemd 서비스 추천)
```

---

## 자동 재처리 (권장)

### 방법 1: Cron 스케줄러

```bash
# crontab 편집
crontab -e

# 5분마다 DLQ 50개씩 재처리
*/5 * * * * cd /path/to/consumer && python dlq_reprocessor.py --max-messages 50 >> dlq.log 2>&1
```

### 방법 2: Systemd 서비스

**파일: /etc/systemd/system/dlq-reprocessor.service**
```ini
[Unit]
Description=DLQ Reprocessor Service
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/path/to/consumer
ExecStart=python dlq_reprocessor.py --group-id systemd-dlq
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 시작
sudo systemctl start dlq-reprocessor

# 상태 확인
sudo systemctl status dlq-reprocessor

# 로그 확인
sudo journalctl -u dlq-reprocessor -f
```

### 방법 3: Docker 컨테이너

```bash
# docker-compose.yml에 추가
services:
  dlq-reprocessor:
    build: ./consumer
    command: python dlq_reprocessor.py --group-id docker-dlq
    environment:
      - KAFKA_BOOTSTRAP=kafka:9092
      - ES_BASE_URL=http://elasticsearch:9200
      - DB_HOST=postgres
      - LOG_LEVEL=INFO
    depends_on:
      - kafka
      - postgres
      - elasticsearch
    restart: always
```

---

## 모범 사례

### 1. 정기적 DLQ 모니터링

```bash
# 매일 오전 2시에 DLQ 메시지 수 확인
0 2 * * * kafka-consumer-groups.sh --bootstrap-server kafka:9092 --group dlq-reprocessor-group --describe | grep news-dlq
```

### 2. 대량 DLQ 메시지 처리 계획

```bash
# 1단계: 현재 DLQ 메시지 수 확인
kafka-run-class.sh kafka.tools.GetOffsetShell \
  --broker-list kafka:9092 \
  --topic news-dlq \
  --time -1

# 2단계: 병렬 재처리 시작 (4개 인스턴스)
for i in {1..4}; do
  python dlq_reprocessor.py --group-id batch-dlq-$i &
done

# 3단계: 완료 대기 및 모니터링
wait
```

### 3. 실패 메시지 별도 보관

```bash
# DLQ 메시지를 파일로 백업
python dlq_reprocessor.py --max-messages 1000 | \
  tee dlq_backup_$(date +%Y%m%d_%H%M%S).log
```

---

## 성능 지표

| 시나리오 | 처리량 | 소요 시간 |
|---------|--------|---------|
| 소규모 (100개) | ~10 msg/sec | 10초 |
| 중규모 (1000개) | ~5 msg/sec | 200초 |
| 대규모 (10000개) | ~3 msg/sec | 3300초 |

**참고:** 외부 서비스(ES, DB) 응답 시간에 따라 변함

---

**마지막 업데이트:** 2026-01-02
