# 🚀 빠른 실행 가이드 (로컬 개발 환경)

## 1단계: 환경 변수 설정

```bash
# .env 파일이 없다면 생성
cp .env.example .env

# .env 파일 편집 (필요시)
# OPENAI_API_KEY=your-api-key-here
```

## 2단계: Docker Compose로 전체 서비스 실행

### 📦 기본 실행 (개발 환경)
```bash
docker-compose up -d
```

이 명령어로 실행되는 서비스:
- ✅ PostgreSQL (pgvector) - 5432 포트
- ✅ Elasticsearch - 9200 포트
- ✅ Kibana - 5601 포트
- ✅ Kafka + Zookeeper - 9092 포트
- ✅ Redis - 6379 포트
- ✅ Django Backend - 8000 포트
- ✅ React Frontend - 3000 포트
- ✅ Nginx - 80 포트

### 🔍 서비스 상태 확인
```bash
docker-compose ps
```

### 📋 로그 확인
```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스만
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 3단계: 초기 데이터 설정

### Django 마이그레이션
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

### Elasticsearch 인덱스 생성
```bash
docker-compose exec backend python search/elasticsearch_setup.py
```

## 4단계: 데이터 파이프라인 실행

### Producer 실행 (RSS 뉴스 수집)
```bash
docker-compose exec producer python produce.py
```

### Consumer 실행 (AI 전처리)
```bash
docker-compose exec consumer python preprocess.py
```

## 5단계: 접속

### 🌐 Frontend (React)
```
http://localhost:3000
```

### 🔧 Backend API (Django)
```
http://localhost:8000/api/
http://localhost:8000/admin/
```

### 📊 Kibana (Elasticsearch UI)
```
http://localhost:5601
```

### 🗃️ PostgreSQL
```
Host: localhost
Port: 5432
Database: newsdb
User: newsuser
Password: newspass
```

## 서비스 중지

```bash
# 서비스 중지 (컨테이너 유지)
docker-compose stop

# 서비스 중지 및 컨테이너 삭제
docker-compose down

# 볼륨까지 삭제 (데이터 초기화)
docker-compose down -v
```

## 🔧 트러블슈팅

### 포트 충돌
이미 사용 중인 포트가 있다면:
```bash
# docker-compose.override.yml 생성해서 포트 변경
# 예: 5432 → 5433
```

### 컨테이너 재시작
```bash
docker-compose restart backend
docker-compose restart frontend
```

### 로그 확인
```bash
# 에러 발생 시
docker-compose logs backend | tail -50
docker-compose logs consumer | tail -50
```

### 데이터베이스 초기화
```bash
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend python manage.py migrate
```

## 📝 개발 모드 vs 프로덕션

### 개발 모드 (현재)
```bash
docker-compose up -d
```

### 프로덕션 모드
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🎯 다음 단계

1. **테스트 실행**
   ```bash
   # Frontend 테스트
   cd frontend-react
   npm test
   npm run test:e2e
   
   # Backend 테스트
   docker-compose exec backend python manage.py test
   ```

2. **Airflow 배치 작업** (선택사항)
   ```bash
   cd batch
   docker-compose up -d
   # http://localhost:8080 접속 (airflow/airflow)
   ```

3. **API 문서 확인**
   - Swagger: http://localhost:8000/swagger/
   - Postman: `api_docs/0515_postman.yaml` 참고

## ⚡ 빠른 명령어 모음

```bash
# 전체 재시작
docker-compose restart

# 특정 서비스 재빌드
docker-compose up -d --build backend

# 실행 중인 컨테이너에서 명령 실행
docker-compose exec backend bash
docker-compose exec postgres psql -U newsuser -d newsdb

# 리소스 정리
docker-compose down
docker system prune -a --volumes
```
