# News Platform Docker README

이 디렉토리는 News Platform의 완전한 Docker 컨테이너화를 위한 파일들을 포함합니다.

## 📁 구조

```
docker/
├── frontend.Dockerfile              # React + Nginx 컨테이너
├── backend.Dockerfile               # Django 백엔드 컨테이너  
├── producer.Dockerfile              # Kafka Producer 컨테이너
├── consumer.Dockerfile              # News Preprocessor 컨테이너
├── nginx/
│   └── nginx.conf                   # Nginx 설정
├── requirements/
│   ├── backend-requirements.txt     # 백엔드 전용 의존성
│   ├── producer-requirements.txt    # Producer 전용 의존성
│   └── consumer-requirements.txt    # Consumer 전용 의존성
├── init-scripts/
│   └── 01-init-database.sh          # PostgreSQL 초기화 스크립트
└── scripts/
    ├── setup.sh                     # 초기 환경 설정
    ├── build.sh                     # 이미지 빌드
    ├── deploy.sh                    # 서비스 배포 및 관리
    └── monitor.sh                   # 모니터링 및 상태 확인
```

## 🚀 빠른 시작

### 1. 초기 설정
```bash
# 실행 권한 부여 (Linux/Mac)
chmod +x docker/scripts/*.sh

# 초기 환경 설정
./docker/scripts/setup.sh
```

### 2. 환경 변수 설정
```bash
# .env 파일 편집
cp .env.example .env
# OpenAI API 키, Django Secret Key 등 실제 값으로 수정
```

### 3. 이미지 빌드
```bash
# 모든 서비스 빌드
./docker/scripts/build.sh

# 특정 서비스만 빌드
./docker/scripts/build.sh frontend
./docker/scripts/build.sh backend
```

### 4. 서비스 배포
```bash
# 개발 모드로 배포
./docker/scripts/deploy.sh start

# 프로덕션 모드로 배포  
./docker/scripts/deploy.sh start production
```

## 🔧 주요 명령어

### 서비스 관리
```bash
# 서비스 시작
./docker/scripts/deploy.sh start [dev|production]

# 서비스 중지
./docker/scripts/deploy.sh stop

# 서비스 재시작
./docker/scripts/deploy.sh restart

# 서비스 상태 확인
./docker/scripts/deploy.sh status
```

### 모니터링
```bash
# 실시간 모니터링
./docker/scripts/monitor.sh monitor

# 특정 서비스 로그 확인
./docker/scripts/monitor.sh logs backend

# 성능 메트릭 확인
./docker/scripts/monitor.sh performance
```

### 데이터베이스 관리
```bash
# 데이터베이스 초기화
./docker/scripts/deploy.sh init-db

# 데이터 백업
./docker/scripts/deploy.sh backup

# 데이터베이스 상태 확인
./docker/scripts/monitor.sh database
```

## 🏗️ 서비스 구성

### 인프라 서비스
- **PostgreSQL + pgvector**: 뉴스 데이터 및 벡터 저장
- **Kafka + Zookeeper**: 메시지 큐잉 시스템
- **Elasticsearch**: 뉴스 검색 및 인덱싱
- **Redis**: 캐싱 및 세션 관리

### 애플리케이션 서비스
- **Frontend**: React + Vite + Nginx (포트 80)
- **Backend**: Django REST API (포트 8000)
- **Producer**: RSS 피드 크롤러
- **Consumer**: 뉴스 전처리 및 AI 분석

## 🌐 접속 정보

### 개발 환경
- **Frontend**: http://localhost
- **Backend API**: http://localhost/api  
- **Django Admin**: http://localhost/admin
- **PostgreSQL**: localhost:5432
- **Kafka**: localhost:29092
- **Elasticsearch**: http://localhost:9200
- **Redis**: localhost:6379

### 프로덕션 환경
포트는 동일하지만 내부 네트워크를 통해 통신합니다.

## 📊 모니터링

### 헬스체크 엔드포인트
- Backend: `http://localhost:8000/health/`
- Elasticsearch: `http://localhost:9200/_cluster/health`
- PostgreSQL: `pg_isready` 명령어로 확인

### 로그 위치
- 컨테이너 로그: `docker-compose logs [서비스명]`
- 애플리케이션 로그: `./logs/` 디렉토리 (볼륨 마운트)

## 🔒 보안 설정

### 환경 변수
중요한 설정은 반드시 `.env` 파일에서 변경:
- `SECRET_KEY`: Django 시크릿 키
- `OPENAI_API_KEY`: OpenAI API 키  
- `POSTGRES_PASSWORD`: 데이터베이스 비밀번호

### SSL/TLS (프로덕션)
```bash
# SSL 인증서 배치
mkdir -p docker/ssl
cp your-cert.pem docker/ssl/cert.pem
cp your-key.pem docker/ssl/key.pem
```

## 🛠️ 트러블슈팅

### 일반적인 문제

1. **컨테이너 시작 실패**
   ```bash
   # 로그 확인
   docker-compose logs [서비스명]
   
   # 컨테이너 상태 확인
   docker-compose ps
   ```

2. **데이터베이스 연결 실패**
   ```bash
   # PostgreSQL 상태 확인
   ./docker/scripts/monitor.sh database
   
   # 수동 연결 테스트
   docker-compose exec postgres psql -U newsuser -d newsdb
   ```

3. **Kafka 연결 문제**
   ```bash
   # Kafka 상태 확인
   ./docker/scripts/monitor.sh kafka
   
   # 토픽 생성 확인
   docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
   ```

4. **메모리 부족**
   ```bash
   # 리소스 사용량 확인
   ./docker/scripts/monitor.sh performance
   
   # 불필요한 컨테이너/이미지 정리
   docker system prune
   ```

### 디버그 모드
```bash
# 개발 모드로 실행 (볼륨 마운트 + 디버그 로그)
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

## 📈 확장 및 최적화

### 수평 확장
```bash
# 특정 서비스 스케일링
docker-compose up --scale consumer=3 -d
```

### 성능 튜닝
- PostgreSQL: `docker/init-scripts/01-init-database.sh`에서 설정 조정
- Elasticsearch: `docker-compose.yml`에서 JVM 힙 크기 조정
- Kafka: 파티션 수 및 복제 계수 조정

## 🔄 업데이트 및 배포

### 코드 업데이트
```bash
# 새 이미지 빌드
./docker/scripts/build.sh

# 무중단 배포
./docker/scripts/deploy.sh restart
```

### 데이터 마이그레이션
```bash
# Django 마이그레이션
docker-compose exec backend python manage.py migrate

# 새로운 인덱스 생성
docker-compose exec backend python manage.py search_index --rebuild
```

## 🆘 지원

문제가 발생하면 다음을 확인하세요:

1. **로그 분석**: `./docker/scripts/monitor.sh logs [서비스명]`
2. **상태 확인**: `./docker/scripts/deploy.sh status`  
3. **리소스 확인**: `./docker/scripts/monitor.sh performance`
4. **설정 검증**: `.env` 파일 및 환경 변수 확인