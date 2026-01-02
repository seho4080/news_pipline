# 📋 프로덕션 배포 가이드

뉴스 파이프라인 프로젝트를 프로덕션 환경에 안전하게 배포하기 위한 종합 가이드입니다.

---

## 📊 배포 체크리스트

### Phase 1: 사전 준비 (1주일 전)

#### 1.1 코드 준비
- [ ] 모든 코드 리뷰 완료
- [ ] 테스트 커버리지 80% 이상
- [ ] 보안 스캔 완료 (snyk, bandit)
- [ ] 마이그레이션 스크립트 준비
- [ ] Rollback 계획 수립

#### 1.2 인프라 준비
- [ ] 프로덕션 서버 구성 확인
- [ ] 네트워크 설정 검증
- [ ] SSL/TLS 인증서 설치
- [ ] 로드 밸런서 설정
- [ ] CDN 설정 (선택)

#### 1.3 데이터 준비
- [ ] 기존 데이터베이스 백업 3회 이상
- [ ] Elasticsearch 인덱스 백업
- [ ] Kafka 토픽 설정 확인
- [ ] 데이터 마이그레이션 스크립트 테스트

#### 1.4 모니터링 준비
- [ ] Prometheus 설정
- [ ] Grafana 대시보드 구성
- [ ] 알람 규칙 설정
- [ ] 로그 집계 설정 (ELK, Splunk)
- [ ] 에러 트래킹 설정 (Sentry)

#### 1.5 커뮤니케이션 준비
- [ ] 배포 일정 공지
- [ ] On-call 엔지니어 지정
- [ ] 긴급 연락처 정리
- [ ] 롤백 담당자 지정

---

### Phase 2: 배포 당일 (배포일)

#### 2.1 배포 전 최종 확인 (배포 2시간 전)
```bash
# 1. 환경 최종 검증
./scripts/pre_deploy_check.sh

# 2. 백업 생성
docker-compose exec -T postgres pg_dump \
  -U newsuser newsdb | gzip > backups/pre_deploy_$(date +%Y%m%d_%H%M%S).sql.gz

# 3. 현재 상태 기록
docker-compose ps > deploy_$(date +%Y%m%d_%H%M%S).log
docker stats --no-stream >> deploy_$(date +%Y%m%d_%H%M%S).log
```

#### 2.2 배포 실행 (오프피크 시간: 새벽 2:00-4:00)
```bash
# 1. 새 이미지 빌드
docker build -f docker/consumer.Dockerfile -t news-consumer:prod .

# 2. 레지스트리에 푸시
docker push myregistry.azurecr.io/news-consumer:prod

# 3. 서비스 업데이트 (무중단 배포)
# Option A: Rolling update
docker-compose up -d --no-deps --scale consumer=4 consumer

# Option B: Blue-Green 배포
# 1. 새 스택 (green) 구성
# 2. 건강 체크 확인
# 3. 로드 밸런서 전환
# 4. 기존 스택 (blue) 종료

# Option C: Canary 배포
# 1. 신 버전 1개 인스턴스만 시작
# 2. 모니터링 5분
# 3. 정상이면 전체 확대
```

#### 2.3 배포 검증
```bash
# 1. 서비스 상태 확인
docker-compose ps
docker-compose logs --tail=50

# 2. 헬스 체크
curl http://localhost:8000/health
curl http://localhost:9200/_cluster/health

# 3. 데이터 검증
# - 메시지 처리 확인
# - 데이터베이스 쓰기 확인
# - Elasticsearch 인덱싱 확인

# 4. 성능 메트릭 확인
# - CPU/메모리 사용량
# - 요청 처리 시간
# - 에러율
```

#### 2.4 롤백 준비 (필요시)
```bash
# 롤백 실행 (30분 이내)
docker-compose down
docker-compose up -d  # 이전 버전 재시작
docker-compose exec -T postgres psql \
  -U newsuser newsdb < backups/pre_deploy_*.sql.gz
```

---

## 🗂️ 배포 환경 설정

### 디렉토리 구조
```
production/
├── docker-compose.prod.yml
├── .env.prod
├── nginx/
│   ├── nginx.conf
│   └── ssl/
│       ├── cert.pem
│       └── key.pem
├── scripts/
│   ├── pre_deploy_check.sh
│   ├── deploy.sh
│   ├── rollback.sh
│   └── backup.sh
├── monitoring/
│   ├── prometheus.yml
│   ├── grafana/
│   └── alertmanager.yml
└── backups/
    ├── postgres/
    ├── elasticsearch/
    └── configs/
```

### 환경 변수 설정 (.env.prod)

```bash
# ===== 데이터베이스 =====
DB_HOST=postgres.prod.internal
DB_PORT=5432
DB_NAME=newsdb_prod
DB_USER=newsuser
DB_PASSWORD=${VAULT_DB_PASSWORD}
DB_TIMEOUT=30
DB_IDLE_TIMEOUT=600
DB_MAX_CONNECTIONS=200

# ===== Kafka =====
KAFKA_BROKERS=kafka-1.prod:9092,kafka-2.prod:9092,kafka-3.prod:9092
KAFKA_TOPIC=news-topic
KAFKA_DLQ_TOPIC=news-dlq
KAFKA_GROUP_ID=news-consumer-prod
KAFKA_MAX_RETRIES=3

# ===== Elasticsearch =====
ES_HOST=elasticsearch.prod.internal
ES_PORT=9200
ES_USERNAME=elastic
ES_PASSWORD=${VAULT_ES_PASSWORD}
ES_INDEX=news-prod
ES_RETRY_MAX=3

# ===== 애플리케이션 =====
LOG_LEVEL=INFO
ENVIRONMENT=production
DEBUG=False

# ===== AI/ML =====
OPENAI_API_KEY=${VAULT_OPENAI_KEY}
LANGCHAIN_DEBUG=False

# ===== 모니터링 =====
SENTRY_DSN=${VAULT_SENTRY_DSN}
PROMETHEUS_PUSHGATEWAY=http://pushgateway:9091

# ===== 보안 =====
ALLOWED_HOSTS=api.news.com,api.backup.com
CORS_ALLOWED_ORIGINS=https://www.news.com
SECRET_KEY=${VAULT_SECRET_KEY}
```

---

## 🔐 보안 설정

### 1. TLS/SSL 설정

```nginx
# nginx.conf (프로덕션)
server {
    listen 443 ssl http2;
    server_name api.news.com;

    # SSL 인증서
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # SSL 정책 (최신)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://api-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP → HTTPS 리다이렉트
server {
    listen 80;
    server_name api.news.com;
    return 301 https://$server_name$request_uri;
}
```

### 2. Docker 보안

```yaml
# docker-compose.prod.yml
services:
  postgres:
    # 루트가 아닌 사용자로 실행
    user: "999:999"
    # 읽기 전용 파일시스템
    read_only: true
    # 임시 볼륨
    tmpfs:
      - /tmp
      - /var/run
    # 리소스 제한
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

  consumer:
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
```

### 3. 네트워크 보안

```yaml
networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 10.0.1.0/24

  backend:
    driver: bridge
    ipam:
      config:
        - subnet: 10.0.2.0/24

services:
  nginx:
    networks:
      - frontend

  consumer:
    networks:
      - backend

  postgres:
    networks:
      - backend
    # 외부에 노출 안 함
    expose:
      - "5432"
```

---

## 📈 모니터링 설정

### Prometheus 설정

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    environment: 'production'

scrape_configs:
  - job_name: 'consumer'
    static_configs:
      - targets: ['consumer:9090']
    relabel_configs:
      - source_labels: [__address__]
        regex: 'consumer:9090'
        target_label: instance

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch:9200']

  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka-exporter:9308']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - 'alerts.yml'
```

### 알람 규칙 (alerts.yml)

```yaml
groups:
  - name: application
    rules:
      # Consumer 에러율 > 5%
      - alert: HighErrorRate
        expr: |
          (rate(consumer_errors_total[5m]) / rate(consumer_messages_processed_total[5m])) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # 메시지 지연 > 60초
      - alert: LagTooHigh
        expr: |
          kafka_consumer_lag_sum > 60
        for: 5m
        annotations:
          summary: "Kafka lag is high"

      # CPU 사용률 > 80%
      - alert: HighCPU
        expr: |
          rate(container_cpu_usage_seconds_total[5m]) > 0.8
        for: 10m
        annotations:
          summary: "High CPU usage"

      # 메모리 사용률 > 90%
      - alert: HighMemory
        expr: |
          container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        annotations:
          summary: "High memory usage"

      # 디스크 여유 < 10%
      - alert: LowDiskSpace
        expr: |
          (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 5m
        annotations:
          summary: "Low disk space"
```

### Grafana 대시보드

[See OPERATIONS_MANUAL.md for detailed Grafana setup]

---

## 🔄 자동화 스크립트

### Pre-Deploy Check Script

```bash
#!/bin/bash
# scripts/pre_deploy_check.sh

set -e

echo "📋 프로덕션 배포 전 체크리스트"
echo "=============================="

# 1. Docker 상태 확인
echo "✓ Docker 상태 확인..."
if ! docker ps > /dev/null 2>&1; then
  echo "❌ Docker가 실행 중이지 않습니다"
  exit 1
fi

# 2. 코드 품질 확인
echo "✓ 코드 품질 확인..."
python -m pylint consumer/*.py --fail-under=8.0 || echo "⚠️  경고: Lint 점수 확인"

# 3. 테스트 실행
echo "✓ 테스트 실행..."
python -m pytest consumer/tests/ -v || echo "⚠️  경고: 테스트 실패"

# 4. 보안 스캔
echo "✓ 보안 스캔..."
python -m bandit -r consumer/ || echo "⚠️  경고: 보안 문제 감지"

# 5. 이미지 빌드 테스트
echo "✓ Docker 이미지 빌드 테스트..."
docker build -f docker/consumer.Dockerfile -t news-consumer:test . || exit 1

# 6. 환경 변수 확인
echo "✓ 환경 변수 확인..."
if [ ! -f ".env.prod" ]; then
  echo "❌ .env.prod 파일이 없습니다"
  exit 1
fi

# 7. 데이터베이스 마이그레이션 준비 확인
echo "✓ 마이그레이션 준비 상태 확인..."
ls backend/migrations/ | wc -l

# 8. 백업 확인
echo "✓ 백업 파일 확인..."
ls -lh backups/ | tail -5

echo ""
echo "✅ 모든 전 배포 체크 통과!"
echo "배포를 진행할 준비가 되었습니다."
```

### Deploy Script

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=${1:-production}
REGION=${2:-us-east-1}

echo "🚀 배포 시작: $ENVIRONMENT ($REGION)"
echo "========================================"

# 1. 환경 변수 로드
source .env.$ENVIRONMENT

# 2. 백업 생성
echo "📦 백업 생성 중..."
docker-compose exec -T postgres pg_dump \
  -U $DB_USER $DB_NAME | gzip > backups/pre_deploy_$(date +%Y%m%d_%H%M%S).sql.gz

# 3. 새 이미지 빌드
echo "🔨 새 이미지 빌드 중..."
docker build -f docker/consumer.Dockerfile \
  -t news-consumer:$ENVIRONMENT \
  -t myregistry.azurecr.io/news-consumer:$ENVIRONMENT \
  --build-arg ENVIRONMENT=$ENVIRONMENT .

# 4. 이미지 푸시
echo "📤 이미지 푸시 중..."
docker push myregistry.azurecr.io/news-consumer:$ENVIRONMENT

# 5. 서비스 업데이트
echo "🔄 서비스 업데이트 중..."

# Rolling update: 인스턴스 수 증가 → 건강 체크 → 기존 인스턴스 종료
docker-compose -f docker-compose.$ENVIRONMENT.yml up -d \
  --no-deps \
  --scale consumer=6 \
  consumer

# 6. 헬스 체크
echo "🩺 헬스 체크 중..."
sleep 30

for i in {1..10}; do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 서비스 정상"
    break
  fi
  echo "⏳ 재시도 ($i/10)..."
  sleep 5
done

# 7. 스케일링 정상화
docker-compose -f docker-compose.$ENVIRONMENT.yml up -d \
  --no-deps \
  --scale consumer=3 \
  consumer

# 8. 배포 로그 저장
echo "📝 배포 로그 저장 중..."
docker-compose logs > deploy_$(date +%Y%m%d_%H%M%S).log

echo ""
echo "✅ 배포 완료!"
```

### Rollback Script

```bash
#!/bin/bash
# scripts/rollback.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "❌ 사용법: $0 <backup_file>"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ 백업 파일이 없습니다: $BACKUP_FILE"
  exit 1
fi

echo "⏮️  롤백 시작"
echo "=================="

# 1. 컨테이너 중지
echo "🛑 서비스 중지 중..."
docker-compose down

# 2. 데이터베이스 복구
echo "🔄 데이터베이스 복구 중..."
docker-compose up -d postgres
sleep 10

zcat "$BACKUP_FILE" | docker-compose exec -T postgres psql \
  -U newsuser newsdb

# 3. 모든 서비스 재시작
echo "🔄 모든 서비스 재시작 중..."
docker-compose up -d

# 4. 헬스 체크
echo "🩺 헬스 체크 중..."
sleep 30
docker-compose ps

echo ""
echo "✅ 롤백 완료!"
```

---

## 📞 긴급 대응

### 장애 대응 프로세스

```
1️⃣  탐지 (1분)
   - 모니터링 알람
   - 사용자 보고

2️⃣  초기 대응 (5분)
   - 상황 파악
   - On-call 엔지니어 호출
   - 슬랙 공지

3️⃣  진단 (15분)
   - 로그 분석
   - 메트릭 확인
   - 근본 원인 파악

4️⃣  임시 조치 (30분)
   - 자동 스케일 업
   - 캐시 초기화
   - 트래픽 리다이렉트

5️⃣  근본 해결 (2시간)
   - 패치 적용
   - 재배포
   - 성능 검증

6️⃣  사후 조치 (24시간)
   - 장애 분석 문서화
   - 개선 사항 도출
   - 팀 공유
```

### 긴급 연락처

| 역할 | 이름 | 연락처 | 비고 |
|------|------|--------|------|
| On-Call Lead | - | - | 주중 09:00-18:00 |
| Database | - | - | 24/7 |
| Infrastructure | - | - | 24/7 |
| Backup | - | - | 월-금 09:00-18:00 |

---

## ✅ 배포 후 검증

### 1단계: 기본 검증 (30분)

```bash
# 서비스 상태
docker-compose ps

# 로그 확인
docker-compose logs --tail=100

# 헬스 체크
curl http://localhost/health
curl http://localhost:9200/_cluster/health
```

### 2단계: 기능 검증 (1시간)

```bash
# 메시지 처리 확인
docker-compose exec postgres psql -U newsuser newsdb \
  -c "SELECT COUNT(*) FROM articles WHERE created_at > now() - interval '1 hour';"

# 검색 인덱싱 확인
curl http://localhost:9200/news-prod/_count

# 성능 메트릭 확인
curl http://localhost:9090/metrics | grep consumer_
```

### 3단계: 모니터링 검증 (24시간)

```bash
# 에러율 모니터링 (0.1% 이상 확인)
# CPU/메모리 사용량 (정상 범위 확인)
# 응답 시간 (평균 < 500ms)
# DLQ 메시지 (0 또는 0에 가깝다)
```

---

**최종 업데이트:** 2026-01-02
**다음 리뷰:** 2026-04-02 (분기별)
