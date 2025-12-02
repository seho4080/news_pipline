# 📰 AI 기반 실시간 뉴스 파이프라인

> 연합뉴스 RSS를 실시간으로 수집하고, AI로 분석·분류하여 사용자에게 맞춤형 뉴스를 제공하는 엔드투엔드 데이터 파이프라인

## 🎯 프로젝트 개요

실시간 뉴스 데이터를 자동으로 수집하고, OpenAI GPT를 활용하여 카테고리 분류, 키워드 추출, 임베딩 생성을 수행한 후, 사용자에게 검색 및 추천 기능을 제공하는 풀스택 뉴스 플랫폼입니다.

### 주요 기능

- **실시간 뉴스 수집**: 연합뉴스 15개 카테고리 RSS 자동 크롤링
- **AI 기반 처리**: GPT-4o-mini를 활용한 자동 카테고리 분류 및 키워드 추출
- **벡터 검색**: pgvector + text-embedding-3-small을 활용한 유사 기사 추천
- **AI 챗봇**: 기사 내용 기반 질의응답
- **품질 모니터링**: 실시간 CSV 로그를 통한 파이프라인 품질 관리
- **개인화**: 사용자별 좋아요, 읽기 기록, 대시보드

## 🏗️ 시스템 아키텍처

```
┌─────────────┐      ┌──────────┐      ┌────────────┐      ┌───────────┐
│  RSS Feeds  │─────▶│ Producer │─────▶│   Kafka    │─────▶│Consumer │
│ (연합뉴스)   │      │ (Python) │      │            │       │ (Python) │
└─────────────┘      └──────────┘      └────────────┘       └────┬─────┘
                                                                 │
                     ┌───────────────────────────────────────────┼─────────┐
                     ▼                                           ▼         ▼
              ┌─────────────┐                            ┌──────────┐  ┌──────────┐
              │   OpenAI    │                            │PostgreSQL│  │Elasticsearch│
              │  GPT-4o-mini│                            │+pgvector │  │          │
              │text-embed-3 │                            └────┬─────┘  └────┬─────┘
              └─────────────┘                                 │             │
                                                              │             │
                     ┌────────────────────────────────────────┴─────────────┤
                     ▼                                                      │
              ┌─────────────┐                                              │
              │   Django    │◀─────────────────────────────────────────────┘
              │   Backend   │
              │   + Redis   │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │    React    │
              │  Frontend   │
              │   + Nginx   │
              └─────────────┘
```

## 🛠️ 기술 스택

### Backend
- **Python 3.11**: Producer, Consumer
- **Django 4.2**: REST API 서버
- **PostgreSQL 15 + pgvector**: 메인 데이터베이스 및 벡터 검색
- **Redis**: 세션 및 캐시 관리
- **Elasticsearch 8.8**: 전문 검색

### Data Pipeline
- **Apache Kafka**: 메시지 큐
- **OpenAI API**: 
  - GPT-4o-mini: 카테고리 분류, 키워드 추출
  - text-embedding-3-small: 벡터 임베딩

### Frontend
- **React 19.1**: UI 프레임워크
- **Vite**: 빌드 도구
- **Nginx**: 웹 서버 및 리버스 프록시

### DevOps
- **Docker & Docker Compose**: 컨테이너화
- **Git**: 버전 관리

## 📦 설치 및 실행

### 사전 요구사항

- Docker & Docker Compose
- OpenAI API Key

### 1. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필수 환경 변수 설정
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_django_secret_key
```

### 2. Docker Compose로 전체 실행

```bash
# 전체 서비스 시작
docker-compose up -d

# 특정 서비스만 재시작
docker-compose restart producer consumer

# 로그 확인
docker-compose logs -f producer
docker-compose logs -f consumer
```

### 3. 서비스 접속

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000/api
- **Elasticsearch**: http://localhost:9200
- **PostgreSQL**: localhost:5432

## 📊 품질 모니터링

파이프라인의 품질을 실시간으로 모니터링할 수 있습니다.

### CSV 로그 확인

```bash
# Producer 통계 (카테고리별 수집 현황)
cat logs/producer_stats.csv

# Consumer 통계 (DB/ES 저장 성공률)
cat logs/consumer_stats.csv

# 실시간 모니터링
tail -f logs/producer_stats.csv
tail -f logs/consumer_stats.csv
```

### 통계 항목

**Producer**:
- 총 전송 성공/실패 건수
- 성공률
- 카테고리별 상세 통계

**Consumer**:
- 소비 메시지 수
- DB 저장 성공률
- Elasticsearch 색인 성공률
- 전처리 성공/실패
- 카테고리별 처리 현황

## 🔧 주요 컴포넌트

### Producer (`producer/produce.py`)
- RSS 피드 15개 카테고리 수집
- 기사 본문 크롤링
- Kafka로 전송
- 매 카테고리 수집마다 통계 CSV 저장

### Consumer (`consumer/news_preprocessor.py`)
- Kafka 메시지 소비
- OpenAI API를 통한 AI 처리:
  - 카테고리 자동 분류
  - 키워드 추출
  - 벡터 임베딩 생성
- PostgreSQL + Elasticsearch 동시 저장
- 5개 메시지마다 통계 CSV 저장

### Backend (`backend/`)
- Django REST Framework 기반 API
- 주요 엔드포인트:
  - `GET /api/news/`: 뉴스 목록 (페이지네이션)
  - `GET /api/news/{id}/`: 뉴스 상세
  - `GET /api/news/{id}/similar/`: 유사 뉴스 추천
  - `PUT /api/news/{id}/likes/`: 좋아요
  - `GET /api/members/likes/`: 좋아요한 기사 목록
  - `GET /api/members/dashboard/`: 개인화 대시보드

### Frontend (`frontend-react/`)
- React 기반 SPA
- 주요 기능:
  - 뉴스 목록 및 상세 보기
  - 카테고리별 필터링
  - 유사 기사 추천
  - 좋아요 및 읽기 기록
  - 개인화 대시보드

## 🚀 주요 기능 상세

### 1. AI 기반 자동 분류
GPT-4o-mini를 활용하여 기사 내용을 분석하고 자동으로 카테고리를 분류합니다.

### 2. 벡터 검색 기반 추천
- text-embedding-3-small로 기사를 벡터화
- pgvector의 코사인 유사도를 사용하여 유사 기사 추천
- 실시간 유사도 계산

### 3. 실시간 데이터 파이프라인
- Kafka를 통한 비동기 처리
- Producer와 Consumer 간 느슨한 결합
- 확장 가능한 아키텍처

### 4. 품질 관리
- 실시간 CSV 로그로 파이프라인 상태 모니터링
- 성공률, 실패율 추적
- 카테고리별 통계

## 📝 개발 가이드

### 로컬 개발 환경 설정

```bash
# Backend 로컬 실행
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver

# Frontend 로컬 실행
cd frontend-react
npm install
npm run dev
```

### 데이터베이스 마이그레이션

```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

### 새로운 슈퍼유저 생성

```bash
docker-compose exec backend python manage.py createsuperuser
```

## 🔍 트러블슈팅

### Producer/Consumer가 시작되지 않을 때
```bash
# 컨테이너 재빌드
docker-compose up -d --build producer consumer

# 로그 확인
docker-compose logs producer consumer
```

### CSV 로그 파일이 생성되지 않을 때
```bash
# logs 디렉토리 권한 확인
ls -la logs/

# 컨테이너 내부 확인
docker exec news-producer ls -la /app/logs/
docker exec news-consumer ls -la /app/logs/
```

### 좋아요 기능 로그아웃 문제
로그인 후 API 토큰이 설정되었는지 확인하세요. 브라우저 개발자 도구의 Network 탭에서 Authorization 헤더를 확인할 수 있습니다.

## 📈 향후 계획

- [ ] Airflow를 통한 배치 처리
- [ ] Grafana + Prometheus 모니터링 대시보드
- [ ] 실시간 알림 기능

## 👥 기여자

- [@seho4080](https://github.com/seho4080)

## 📄 라이선스

This project is licensed under the MIT License.

## 🙏 감사의 글

- 연합뉴스 RSS 제공
- OpenAI API
- 오픈소스 커뮤니티

