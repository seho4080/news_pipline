# 🐳 Docker Compose 최적화 가이드

프로덕션 환경에서 안정적으로 운영하기 위한 Docker Compose 설정 및 최적화 방법입니다.

---

## ✅ 현재 상태 확인

### 기본 명령어

```bash
# 1. 전체 서비스 상태 확인
docker-compose ps

# 2. 서비스별 로그 확인
docker-compose logs -f consumer
docker-compose logs -f postgres

# 3. 리소스 사용량 확인
docker stats --no-stream

# 4. 헬스 체크
docker-compose run --rm healthcheck

# 5. 정상 종료
docker-compose down

# 6. 강제 정리 (주의!)
docker-compose down -v
```

---

## 🔧 성능 최적화

### 1. Consumer 스케일링

**단일 인스턴스 (기본)**
```yaml
services:
  consumer:
    image: news-consumer:latest
    container_name: news-consumer
```

**다중 인스턴스 (권장)**
```yaml
services:
  consumer:
    image: news-consumer:latest
    deploy:
      replicas: 3  # 3개 인스턴스
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

**사용 방법:**
```bash
# 스케일링 적용
docker-compose up -d --scale consumer=3

# 특정 인스턴스 로그 확인
docker-compose logs consumer_1
docker-compose logs consumer_2
docker-compose logs consumer_3
```

### 2. Kafka 파티션 증가

```bash
# 파티션 수 확인
docker exec news-kafka kafka-topics.sh \
  --list --bootstrap-server localhost:9092

# 파티션 증가 (1 → 3)
docker exec news-kafka kafka-topics.sh \
  --alter --topic news-topic \
  --partitions 3 \
  --bootstrap-server localhost:9092

# DLQ 파티션도 증가
docker exec news-kafka kafka-topics.sh \
  --alter --topic news-dlq \
  --partitions 2 \
  --bootstrap-server localhost:9092

# 확인
docker exec news-kafka kafka-topics.sh \
  --describe --topic news-topic \
  --bootstrap-server localhost:9092
```

**권장 설정:**
- **파티션 수** = Consumer 인스턴스 수
  - 1개 Consumer → 1 파티션
  - 3개 Consumer → 3 파티션

### 3. Elasticsearch 최적화

```yaml
services:
  elasticsearch:
    environment:
      # JVM 메모리 설정
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      
      # 성능 튜닝
      - "indices.memory.index_buffer_size=30%"
      - "thread_pool.bulk.queue_size=300"
      - "thread_pool.search.queue_size=1000"
      
      # 클러스터 설정
      - "cluster.name=news-cluster"
      - "node.name=es-node-1"
      - "discovery.type=single-node"
      
    mem_limit: 1g
    memswap_limit: 1g
```

### 4. PostgreSQL 최적화

```yaml
services:
  postgres:
    command: >
      postgres
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c maintenance_work_mem=64MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100
      -c random_page_cost=1.1
      -c effective_io_concurrency=200
      -c work_mem=4MB
      -c min_wal_size=1GB
      -c max_wal_size=4GB
    
    environment:
      POSTGRES_INITDB_ARGS: "-c max_connections=200"
```

---

## 📦 리소스 관리

### CPU & 메모리 제한

```yaml
services:
  consumer:
    deploy:
      resources:
        limits:
          cpus: '1'          # 최대 1 CPU
          memory: 512M       # 최대 512MB
        reservations:
          cpus: '0.5'        # 예약 0.5 CPU
          memory: 256M       # 예약 256MB

  postgres:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  elasticsearch:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 디스크 관리

```bash
# 디스크 사용량 확인
df -h

# Docker 이미지 정리 (사용되지 않는 것)
docker image prune -a

# 컨테이너 로그 정리
docker system prune

# 볼륨 정리
docker volume prune

# 전체 정리 (주의!)
docker system prune -a
```

### 볼륨 설정

```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/data/postgres  # 외부 마운트 지점

  es_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/data/elasticsearch

  kafka_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/data/kafka
```

---

## 🔍 모니터링

### 실시간 모니터링

```bash
# 1. 리소스 사용량 실시간 확인
docker stats --no-stream

# 2. 컨테이너 프로세스 확인
docker top news-consumer
docker top news-postgres

# 3. 네트워크 통계
docker network inspect news-network

# 4. 볼륨 사용량
docker volume inspect postgres_data
docker volume inspect es_data
```

### 헬스 체크 추가

```yaml
services:
  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U newsuser -d newsdb"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s

  elasticsearch:
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health | grep -q '\"status\":\"yellow\\|green\"' || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s

  kafka:
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions.sh", "--bootstrap-server", "localhost:9092"]
      interval: 30s
      timeout: 10s
      retries: 5
```

---

## 🚀 배포 환경별 설정

### 로컬 개발 환경

```yaml
# docker-compose.yml
version: "3.8"

services:
  postgres:
    image: pgvector/pgvector:pg15
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: newspass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms512m -Xmx512m

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    ports:
      - "9092:9092"
    depends_on:
      - zookeeper

  consumer:
    build: ./consumer
    depends_on:
      - postgres
      - elasticsearch
      - kafka
    environment:
      - LOG_LEVEL=DEBUG

volumes:
  postgres_data:
```

### 스테이징 환경

```yaml
# docker-compose.staging.yml
version: "3.8"

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '1'
          memory: 1G

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  consumer:
    image: news-consumer:latest
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 512M
    environment:
      - LOG_LEVEL=INFO

networks:
  default:
    driver: bridge
    driver_opts:
      com.docker.network.driver.mtu: 1450
```

### 프로덕션 환경

```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  postgres:
    image: pgvector/pgvector:pg15
    restart: always
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "10"

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    restart: always
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms1g -Xmx1g
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=${ES_PASSWORD}
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "10"

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  consumer:
    image: news-consumer:latest
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    environment:
      - LOG_LEVEL=INFO
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "20"

networks:
  default:
    driver: bridge
    driver_opts:
      com.docker.network.driver.mtu: 1450

volumes:
  postgres_data:
    driver: local
  es_data:
    driver: local
```

---

## 🔄 자동 백업 & 복구

### 백업 스크립트

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# PostgreSQL 백업
docker-compose exec -T postgres pg_dump \
  -U newsuser newsdb \
  | gzip > "$BACKUP_DIR/postgres.sql.gz"

echo "✅ PostgreSQL 백업 완료: $BACKUP_DIR/postgres.sql.gz"

# Elasticsearch 스냅샷 (선택)
# curl -X PUT "http://localhost:9200/_snapshot/backup/$(date +%Y%m%d_%H%M%S)"

# 7일 이상 된 백업 삭제
find backups -type d -mtime +7 -exec rm -rf {} \;
```

### 복구 스크립트

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ 백업 파일 없음: $BACKUP_FILE"
  exit 1
fi

echo "🔄 복구 중: $BACKUP_FILE"

# PostgreSQL 복구
zcat "$BACKUP_FILE" | docker-compose exec -T postgres psql \
  -U newsuser newsdb

echo "✅ 복구 완료"
```

---

## 📝 운영 Checklist

### 배포 전
- [ ] 로컬에서 `docker-compose up -d` 테스트
- [ ] 모든 서비스가 healthy 상태인지 확인
- [ ] 환경변수 점검 (.env 파일)
- [ ] 리소스 제한 설정 확인
- [ ] 볼륨 마운트 경로 확인

### 배포 후
- [ ] 모든 서비스 헬스 체크
- [ ] 로그 모니터링
- [ ] 초기 데이터 로드 확인
- [ ] API 응답 테스트
- [ ] 백업 정상 작동 확인

### 정기 점검 (월 1회)
- [ ] 디스크 여유 공간 확인
- [ ] 로그 크기 점검
- [ ] 성능 메트릭 분석
- [ ] 보안 업데이트 확인
- [ ] 백업 검증

---

## 🆘 트러블슈팅

### 컨테이너가 자꾸 재시작됨

```bash
# 로그 확인
docker-compose logs consumer

# 메모리 부족 확인
docker stats --no-stream consumer

# 리소스 제한 증가
docker-compose.yml에서 memory 값 증가

# 컨테이너 재시작
docker-compose restart consumer
```

### 느린 성능

```bash
# 병목 지점 찾기
docker stats --no-stream

# 네트워크 통계
docker network inspect news-network

# 디스크 I/O 확인
docker exec postgres iostat -x 1 5

# 최적화 (위의 성능 최적화 섹션 참고)
```

### 디스크 부족

```bash
# 사용량 확인
docker system df

# 이미지 정리
docker image prune -a

# 로그 정리
docker system prune

# 실제 필요한 경우 외부 저장소 마운트
# docker-compose.yml의 volumes 경로 변경
```

---

**마지막 업데이트:** 2026-01-02
