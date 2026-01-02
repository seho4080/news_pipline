# ✅ 배포 체크리스트

프로덕션 배포 전에 확인할 항목들입니다.

---

## 🔍 코드 검증

- [ ] 모든 import 문 확인 (requirements.txt와 일치)
- [ ] 환경변수 기본값 설정 확인
- [ ] 에러 처리 (try-except) 모두 적용됨
- [ ] 타임아웃 설정 확인 (DB, ES, HTTP)
- [ ] 로깅 레벨 설정 (DEBUG/INFO 구분)

---

## 🗂️ 설정 파일

- [ ] `.env.example` 작성됨
- [ ] 모든 환경변수가 기본값을 가짐
- [ ] 민감한 정보(비밀번호) 하드코딩 안됨
- [ ] Kubernetes secrets 또는 vault 준비 완료

---

## 📦 의존성 관리

- [ ] `requirements.txt` 최신 버전 지정
  ```bash
  pip freeze > requirements.txt
  ```
- [ ] 불필요한 패키지 제거
- [ ] 의존성 호환성 검증
  ```bash
  pip install -r requirements.txt
  python -c "import confluent_kafka, psycopg2, requests"
  ```

---

## 🗄️ 데이터베이스

- [ ] PostgreSQL 테이블 생성 스크립트 준비
  ```sql
  CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    url VARCHAR(1000) UNIQUE NOT NULL,
    writer VARCHAR(100),
    write_date TIMESTAMP,
    category VARCHAR(50),
    keywords TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
  );
  ```
- [ ] 인덱스 생성됨
  ```sql
  CREATE INDEX idx_articles_url ON articles(url);
  CREATE INDEX idx_articles_category ON articles(category);
  CREATE INDEX idx_articles_write_date ON articles(write_date);
  ```
- [ ] ON CONFLICT 처리 검증 (멱등성)
- [ ] 연결 풀 설정 적절함

---

## 🔎 검색 엔진 (Elasticsearch)

- [ ] Elasticsearch 인덱스 매핑 생성
  ```json
  PUT /news
  {
    "mappings": {
      "properties": {
        "title": { "type": "text", "analyzer": "nori" },
        "content": { "type": "text", "analyzer": "nori" },
        "url": { "type": "keyword" },
        "category": { "type": "keyword" }
      }
    }
  }
  ```
- [ ] 한글 분석기 (nori) 설치됨
- [ ] 디스크 여유 공간 충분
- [ ] 인덱스 설정 (샤드, 레플리카) 최적화됨

---

## 📨 메시지 큐 (Kafka)

- [ ] 토픽 생성됨
  ```bash
  kafka-topics.sh --create \
    --topic news-topic \
    --partitions 3 \
    --replication-factor 1 \
    --bootstrap-server kafka:9092
  
  kafka-topics.sh --create \
    --topic news-dlq \
    --partitions 1 \
    --replication-factor 1 \
    --bootstrap-server kafka:9092
  ```
- [ ] 파티션 수 성능에 맞춤 조정
- [ ] Consumer group ID 고유함 (`python-news-group`)
- [ ] 리텐션 정책 설정
  - news-topic: 7일 (기본)
  - news-dlq: 30일 (재처리 시간 확보)

---

## 🚀 배포 준비

- [ ] Docker 이미지 빌드 및 테스트
  ```bash
  docker build -f docker/consumer.Dockerfile -t news-consumer:latest .
  docker run -it --rm \
    --env-file .env \
    news-consumer:latest
  ```
- [ ] docker-compose.yml 작성 및 테스트
  ```bash
  docker-compose up -d
  docker-compose logs -f consumer
  ```
- [ ] Kubernetes 매니페스트 준비 (권장)
  ```yaml
  kind: Deployment
  metadata:
    name: news-consumer
  spec:
    replicas: 2
    template:
      spec:
        containers:
        - name: consumer
          image: news-consumer:latest
          envFrom:
          - configMapRef:
              name: consumer-config
          - secretRef:
              name: consumer-secret
  ```

---

## 📊 모니터링 & 로깅

- [ ] 로그 저장 경로 생성됨
  ```bash
  mkdir -p /app/logs
  chmod 777 /app/logs
  ```
- [ ] 로그 로테이션 설정
  ```bash
  # /etc/logrotate.d/news-consumer
  /app/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
  }
  ```
- [ ] CSV 통계 모니터링 대시보드 준비
- [ ] 알림 설정 (Slack, Email 등)
  ```bash
  # 에러 발생 시 알림
  grep "ERROR" logs/consumer.log | \
    curl -X POST -d "Consumer Error: $(cat)" \
    https://hooks.slack.com/services/YOUR/WEBHOOK
  ```
- [ ] Prometheus 메트릭 (선택)
- [ ] Grafana 대시보드 (선택)

---

## 🧪 테스트

### 단위 테스트

- [ ] 전처리 함수 테스트
  ```bash
  python -m pytest tests/test_preprocess.py -v
  ```
- [ ] DB 쿼리 테스트
  ```bash
  python -m pytest tests/test_db.py -v
  ```
- [ ] ES 쿼리 테스트
  ```bash
  python -m pytest tests/test_es.py -v
  ```

### 통합 테스트

- [ ] 로컬 환경에서 전체 파이프라인 테스트
  ```bash
  docker-compose up -d
  python producer/produce.py --count 100
  sleep 30
  python scripts/validate_consumer.py
  ```
- [ ] DLQ 재처리 테스트
  ```bash
  python dlq_reprocessor.py --max-messages 10
  ```
- [ ] Graceful shutdown 테스트
  ```bash
  python news_preprocessor.py &
  PID=$!
  sleep 5
  kill -TERM $PID
  wait $PID
  ```

### 부하 테스트

- [ ] 동시 메시지 처리 테스트
  ```bash
  # 초당 1000개 메시지 전송
  python producer/produce.py --rate 1000 --duration 60
  ```
- [ ] 메모리 사용량 모니터링
  ```bash
  watch -n 1 'ps aux | grep news_preprocessor'
  ```
- [ ] CPU 사용량 모니터링
  ```bash
  top -p $(pgrep -f news_preprocessor)
  ```

---

## 🔐 보안

- [ ] DB 사용자 권한 최소화
  ```sql
  CREATE USER consumer WITH PASSWORD 'strong_password';
  GRANT SELECT, INSERT, UPDATE ON articles TO consumer;
  ```
- [ ] 비밀번호 environment variable로 관리
- [ ] SSL/TLS 설정 (프로덕션)
  - PostgreSQL: `sslmode=require`
  - Elasticsearch: HTTPS 활성화
  - Kafka: SASL/SSL 인증
- [ ] VPC/네트워크 분리
- [ ] 정기 보안 업데이트
  ```bash
  pip install --upgrade pip
  pip install --upgrade -r requirements.txt
  ```

---

## 📈 성능 최적화

- [ ] DB 연결 풀 크기 조정
  ```env
  DB_MIN_CONN=2
  DB_MAX_CONN=10
  ```
- [ ] Kafka 파티션 수 → Consumer 수와 일치
- [ ] 배치 처리 고려 (선택)
- [ ] 캐싱 전략 수립 (Redis 등)

---

## 📋 문서화

- [ ] README.md 완성
- [ ] QUICKSTART.md 완성
- [ ] DLQ_GUIDE.md 완성
- [ ] 환경변수 설정 가이드 작성
- [ ] 운영 매뉴얼 작성
  - [ ] 일일 점검 사항
  - [ ] 장애 대응 절차
  - [ ] 롤백 절차
- [ ] API 문서 (선택)

---

## 🚨 장애 대응

- [ ] 온콜 일정 수립
- [ ] 장애 대응 플레이북 작성
  - Consumer 다운
  - DB 연결 끊김
  - ES 다운
  - Kafka 다운
- [ ] 자동 복구 스크립트 준비
  ```bash
  #!/bin/bash
  if ! pgrep -f news_preprocessor > /dev/null; then
    systemctl restart news-consumer
    echo "Consumer restarted" | mail -s "Alert" ops@example.com
  fi
  ```
- [ ] 정기 재해복구 훈련

---

## ✅ 최종 확인

- [ ] 모든 환경변수 설정됨
- [ ] 모든 외부 서비스 정상 작동
- [ ] 샘플 데이터로 E2E 테스트 통과
- [ ] 성능 지표 수집됨
- [ ] 백업 전략 수립됨
- [ ] 운영팀 교육 완료
- [ ] 배포 승인 획득

---

## 배포 후 모니터링

### 1시간

- [ ] Consumer 정상 작동 확인
- [ ] 로그에 에러 없음
- [ ] CSV 통계 생성됨

### 24시간

- [ ] 메모리 사용량 안정적
- [ ] CPU 사용량 예상 범위 내
- [ ] DB/ES 응답 시간 정상
- [ ] DLQ 메시지 누적 없음

### 1주일

- [ ] 처리량 일관성 확인
- [ ] 에러율 0% 근처
- [ ] 시스템 안정성 평가
- [ ] 성능 최적화 검토

---

**배포 날짜:** ________________

**배포자:** ________________

**승인자:** ________________

**비고:** 

