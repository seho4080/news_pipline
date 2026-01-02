# 📋 프로덕션 운영 매뉴얼

실시간 뉴스 파이프라인의 일일 운영, 모니터링, 장애 대응을 위한 가이드입니다.

---

## 📊 일일 운영 체크리스트

### 오전 (08:00)

```bash
# 1. 시스템 헬스 체크
docker-compose ps

# 2. 서비스 로그 확인 (에러 검색)
docker-compose logs --tail 100 consumer | grep -i "error\|warn"
docker-compose logs --tail 100 kafka | grep -i "error"
docker-compose logs --tail 100 postgres | grep -i "error"

# 3. Consumer 처리량 확인
tail -f logs/consumer_stats.csv | head -5

# 4. Kafka Consumer Lag 확인
docker exec news-kafka kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group python-news-group --describe

# 5. PostgreSQL 테이블 크기 확인
docker exec news-postgres psql -U newsuser -d newsdb -c \
  "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) \
   FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') \
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# 6. Elasticsearch 클러스터 상태
curl -s http://localhost:9200/_cluster/health | jq
```

### 오후 (17:00)

```bash
# 1. 일일 처리 통계 리포트
echo "=== 처리 통계 ==="
tail -1 logs/consumer_stats.csv

# 2. DLQ 메시지 누적 확인
docker exec news-kafka kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group dlq-group --describe --topic news-dlq

# 3. 에러 로그 정리
grep "ERROR" logs/*.log | wc -l

# 4. 디스크 사용량 확인
docker exec news-postgres psql -U newsuser -d newsdb -c \
  "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database \
   WHERE datname NOT IN ('template0', 'template1', 'postgres');"

# 5. DB 연결 확인
docker exec news-postgres psql -U newsuser -d newsdb -c "SELECT * FROM pg_stat_activity WHERE datname='newsdb';" | wc -l
```

### 저녁 (22:00)

```bash
# 1. 시스템 리소스 확인
docker stats --no-stream

# 2. Consumer 메모리 사용량
docker exec news-consumer ps aux | grep news_preprocessor

# 3. 백업 확인
ls -lh backups/postgres_*.sql.gz | tail -1

# 4. 다음날 준비
# - 로그 아카이빙
tar -czf logs/archive/$(date +%Y%m%d)_logs.tar.gz logs/*.csv logs/*.log

# - 통계 초기화 (선택)
# rm logs/consumer_stats.csv
```

---

## 🚨 모니터링 & 알림 설정

### Consumer Lag 모니터링

```bash
#!/bin/bash
# monitor_lag.sh - 5분마다 실행

LAG=$(docker exec news-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group python-news-group \
  --describe | grep news-topic | awk '{print $5}')

if [ "$LAG" -gt 1000 ]; then
  echo "⚠️  Lag 증가 감지: $LAG" | mail -s "Kafka Lag Alert" ops@example.com
fi
```

**Cron 설정:**
```bash
*/5 * * * * /path/to/monitor_lag.sh
```

### 디스크 사용량 알림

```bash
#!/bin/bash
# monitor_disk.sh

USAGE=$(docker exec news-postgres psql -U newsuser -d newsdb -c \
  "SELECT pg_database_size('newsdb')/1024/1024/1024;" | grep -o '[0-9]*')

if [ "$USAGE" -gt 50 ]; then
  echo "⚠️  DB 크기 초과: ${USAGE}GB" | mail -s "Disk Space Alert" ops@example.com
fi
```

### Elasticsearch Health 모니터링

```bash
#!/bin/bash
# monitor_es.sh

HEALTH=$(curl -s http://localhost:9200/_cluster/health | jq -r '.status')

if [ "$HEALTH" != "green" ]; then
  echo "⚠️  ES 상태 비정상: $HEALTH" | mail -s "Elasticsearch Alert" ops@example.com
fi
```

---

## 🔧 일반적인 문제 해결

### 1. Consumer 멈춤

**증상:**
- Consumer 로그 없음
- Lag 증가

**진단:**
```bash
# Consumer 프로세스 확인
docker ps | grep consumer

# 최근 로그 확인
docker logs --tail 50 news-consumer | tail -20

# 메모리 확인
docker stats news-consumer --no-stream
```

**해결:**
```bash
# 1단계: 재시작
docker restart news-consumer

# 2단계: 데이터 손실 없이 재배포
docker-compose down consumer
docker-compose up -d consumer

# 3단계: 전체 스택 재시작
docker-compose restart
```

### 2. Kafka Consumer Lag 증가

**증상:**
- `Lag` 값이 계속 증가
- Consumer가 메시지를 처리하지 못함

**진단:**
```bash
# Consumer Lag 확인
kafka-consumer-groups --bootstrap-server kafka:9092 \
  --group python-news-group --describe

# Consumer 상태 확인
docker logs news-consumer | grep -i "error\|fail"

# 외부 서비스 상태 확인
curl -s http://localhost:9200/_cluster/health  # ES
psql -h localhost -U newsuser -d newsdb -c "SELECT 1"  # DB
```

**해결:**
```bash
# 1. ES 복구
curl -X PUT "http://localhost:9200/_cluster/settings" \
  -H 'Content-Type: application/json' \
  -d '{"transient": {"cluster.routing.allocation.enable": "all"}}'

# 2. DB 최적화
VACUUM FULL;
REINDEX DATABASE newsdb;

# 3. Consumer 동시성 증가
# docker-compose.yml에서 replicas 증가
```

### 3. PostgreSQL 응답 느림

**증상:**
- Consumer DB 저장 느림
- Connection timeout

**진단:**
```bash
# 활성 연결 확인
psql -h localhost -U newsuser -d newsdb -c \
  "SELECT pid, usename, query FROM pg_stat_activity WHERE datname='newsdb' AND state='active';"

# 오래 실행 중인 쿼리
psql -h localhost -U newsuser -d newsdb -c \
  "SELECT pid, query_start, query FROM pg_stat_activity WHERE duration > INTERVAL '5 minute';"

# 테이블 크기 확인
psql -h localhost -U newsuser -d newsdb -c \
  "SELECT tablename, pg_size_pretty(pg_total_relation_size('articles')) FROM pg_tables;"
```

**해결:**
```bash
# 1. 인덱스 재구축
psql -h localhost -U newsuser -d newsdb -c "REINDEX TABLE articles;"

# 2. 통계 업데이트
psql -h localhost -U newsuser -d newsdb -c "ANALYZE articles;"

# 3. Dead tuple 정리
psql -h localhost -U newsuser -d newsdb -c "VACUUM FULL articles;"

# 4. 연결 풀 재시작
docker restart news-consumer
```

### 4. Elasticsearch 디스크 부족

**증상:**
- ES가 읽기 전용 모드로 전환
- 인덱싱 실패

**진단:**
```bash
# ES 상태
curl -s http://localhost:9200/_cluster/health | jq

# 샤드 상태
curl -s http://localhost:9200/_cluster/allocation/explain | jq

# 디스크 사용량
curl -s http://localhost:9200/_nodes/stats/fs | jq '.nodes[] | {name, total_in_bytes, available_in_bytes}'
```

**해결:**
```bash
# 1. 읽기 전용 해제
curl -X PUT "http://localhost:9200/_cluster/settings" \
  -H 'Content-Type: application/json' \
  -d '{"transient": {"cluster.routing.allocation.disk.threshold_enabled": false}}'

# 2. 오래된 인덱스 삭제
curl -X DELETE "http://localhost:9200/news-2025-01*"

# 3. 샤드 재배치
curl -X PUT "http://localhost:9200/_cluster/settings" \
  -H 'Content-Type: application/json' \
  -d '{"transient": {"cluster.routing.rebalance.enable": "all"}}'
```

---

## 📈 성능 최적화

### Consumer 처리량 증가

```bash
# 1. 인스턴스 수 증가 (docker-compose.yml)
services:
  consumer:
    deploy:
      replicas: 3  # 기본값: 1

# 2. Kafka 파티션 증가
kafka-topics.sh --alter --topic news-topic \
  --partitions 3 --bootstrap-server kafka:9092

# 3. 배치 크기 조정 (news_preprocessor.py)
# SAVE_INTERVAL = 10  # 5에서 10으로 증가

# 4. DB 연결 풀 증가
# DB_MAX_CONN=20  (기본값: 5)
```

### Database 최적화

```sql
-- 1. 인덱스 추가
CREATE INDEX idx_articles_write_date ON articles(write_date DESC);

-- 2. 파티셔닝 (대규모)
ALTER TABLE articles PARTITION BY RANGE (YEAR(write_date)) (
  PARTITION p2024 VALUES LESS THAN (2025),
  PARTITION p2025 VALUES LESS THAN (2026)
);

-- 3. 쿼리 최적화
EXPLAIN ANALYZE SELECT * FROM articles WHERE url = 'test';

-- 4. 통계 업데이트
ANALYZE articles;
```

### Elasticsearch 최적화

```bash
# 1. 샤드/레플리카 조정
curl -X PUT "http://localhost:9200/news/_settings" \
  -H 'Content-Type: application/json' \
  -d '{
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "30s"
  }'

# 2. 벌크 인덱싱
# DLQ 메시지를 벌크로 처리

# 3. 구식 인덱스 정리
curl -X DELETE "http://localhost:9200/news-*"
```

---

## 🔒 보안 & 백업

### 정기 백업

```bash
#!/bin/bash
# backup.sh - 매일 01:00에 실행

BACKUP_DIR="backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# PostgreSQL 백업
docker exec news-postgres pg_dump \
  -U newsuser newsdb \
  | gzip > "$BACKUP_DIR/postgres_newsdb.sql.gz"

# Elasticsearch 스냅샷
curl -X PUT "http://localhost:9200/_snapshot/backup" \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "fs",
    "settings": {
      "location": "/path/to/snapshots"
    }
  }'

# 7일 이상 된 백업 삭제
find backups -type f -mtime +7 -delete

echo "✅ Backup completed at $(date)"
```

**Cron 설정:**
```bash
0 1 * * * /path/to/backup.sh
```

### 로그 보관

```bash
#!/bin/bash
# archive_logs.sh

ARCHIVE_DIR="logs/archive/$(date +%Y/%m)"
mkdir -p "$ARCHIVE_DIR"

# 로그 압축
tar -czf "$ARCHIVE_DIR/$(date +%d).tar.gz" \
  logs/*.log logs/*.csv

# 90일 이상 된 아카이브 삭제
find logs/archive -type f -mtime +90 -delete
```

---

## 📞 온콜(On-Call) 절차

### 장애 신고 (1단계)

```
[ ] 날짜/시간 기록
[ ] 증상 확인 (Lag, Error, Performance)
[ ] 영향받는 컴포넌트 파악
[ ] 관련 팀에 알림
```

### 즉시 조치 (2단계)

```bash
# 1. 시스템 상태 확인
docker-compose ps
docker-compose logs --tail 100

# 2. 빠른 진단
curl http://localhost:9200/_cluster/health
psql -h localhost -U newsuser -d newsdb -c "SELECT 1"
kafka-consumer-groups --describe

# 3. 임시 조치
docker restart news-consumer  # Consumer 재시작
docker-compose up -d           # 스택 재시작
```

### 상세 조사 (3단계)

```bash
# 근본 원인 찾기
docker logs news-consumer --since 30m > incident_logs.txt
tail -f logs/consumer_stats.csv

# 필요시 롤백
git revert <commit-hash>
docker-compose up -d
```

### 사후 처리 (4단계)

```
[ ] 장애 요약 작성
[ ] 근본 원인 분석 (RCA)
[ ] 개선 계획 수립
[ ] 팀 회의 진행
[ ] 예방 조치 구현
```

---

## 📝 운영 문서 템플릿

### 일일 리포트

```
# 2026-01-02 운영 리포트

## 📊 처리량
- 총 메시지: 10,500개
- DB 성공: 10,450개 (99.5%)
- ES 실패: 50개 (DLQ로 전송됨)

## 🔧 이슈
- [ ] 특별한 이슈 없음
- [ ] Consumer Lag 최대: 120개

## 📈 시스템 리소스
- DB: 2.5GB / 100GB
- ES: 5.2GB / 50GB
- Kafka: 1.8GB

## ✅ 완료 항목
- DLQ 50개 재처리 완료
- 인덱스 최적화 진행
```

### 주간 리포트

```
# 2026-01-02 주간 리포트

## 📊 누적 통계
- 총 처리: 72,000개
- 성공률: 99.2%
- 평균 처리량: 10,286 msg/day

## 🚨 장애 이력
- 2026-01-01 14:30: ES 디스크 부족 (15분)
- 2026-01-02 08:00: Consumer 메모리 누수 (재시작으로 해결)

## 📋 개선 사항
- [ ] ES 샤드 수 3개로 증가
- [ ] DB 인덱스 재구축 완료
- [ ] Consumer 메모리 프로파일링

## 📅 다음주 계획
- 모니터링 대시보드 구축
- 자동 장애 복구 스크립트 작성
- 부하 테스트 수행
```

---

## 🎓 운영팀 교육 체크리스트

- [ ] 장애 대응 절차 이해
- [ ] 주요 명령어 실행 능력
  - `docker-compose ps`
  - `docker logs`
  - `curl` (ES 헬스 체크)
  - `psql` (DB 확인)
  - Kafka CLI 도구 사용
- [ ] 모니터링 대시보드 사용법
- [ ] 온콜 연락처 및 에스컬레이션 절차
- [ ] 백업/복구 절차
- [ ] 문서 위치 및 접근 방법

---

**마지막 업데이트:** 2026-01-02
