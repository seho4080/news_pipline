# 🌐 Backend API 가이드

뉴스 파이프라인 프로젝트의 Django 기반 Backend API 서버 완벽 가이드입니다.

---

## 🏗️ 아키텍처 개요

### Backend 역할
```
┌─────────────────────────────────────────────────┐
│              Backend API Server                 │
│         (Django + Django REST Framework)        │
├─────────────────────────────────────────────────┤
│  • 기사 데이터 관리 (CRUD)                        │
│  • 사용자 인증/인가                              │
│  • API 응답 포맷팅                              │
│  • 데이터 검증                                   │
│  • 캐싱 (Redis)                                 │
└─────────────────────────────────────────────────┘
         ↓                              ↓
    PostgreSQL              Elasticsearch
    (원본 데이터)            (검색 인덱싱)
```

### 모듈 구조

```
backend/
├── myproject/              # Django 프로젝트 설정
│   ├── settings.py        # 데이터베이스, 앱, 미들웨어
│   ├── urls.py            # 라우팅
│   ├── wsgi.py            # 프로덕션 배포
│   └── response.py        # API 응답 포맷
│
├── members/               # 사용자 관리 모듈
│   ├── models.py          # User, Profile 모델
│   ├── serializers.py     # API 직렬화
│   ├── views.py           # 로그인, 회원가입, 프로필
│   ├── urls.py            # 라우트
│   └── tests.py           # 유닛 테스트
│
├── mynews/                # 기사 관리 모듈
│   ├── models.py          # Article, Category, Keyword
│   ├── serializers.py     # 기사 API 포맷
│   ├── views.py           # 기사 조회, 검색, 필터링
│   ├── urls.py            # 라우트
│   └── tests.py           # 유닛 테스트
│
├── manage.py              # Django CLI
├── requirements.txt       # Python 패키지
└── db_test.py            # 데이터베이스 연결 테스트
```

---

## 🚀 빠른 시작

### 1단계: 환경 설정

```bash
# 저장소 클론
git clone <repo-url>
cd backend

# Python 가상 환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2단계: 데이터베이스 설정

```bash
# 마이그레이션 생성
python manage.py makemigrations

# 마이그레이션 적용
python manage.py migrate

# 슈퍼유저 생성
python manage.py createsuperuser
```

### 3단계: 서버 실행

```bash
# 개발 서버 시작
python manage.py runserver 0.0.0.0:8000

# 서버 확인
curl http://localhost:8000/api/health/
```

---

## 📡 API 엔드포인트

### 인증 (Members)

#### 회원가입
```http
POST /api/members/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepass123",
  "first_name": "John",
  "last_name": "Doe"
}

응답 (201 Created):
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 로그인
```http
POST /api/members/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepass123"
}

응답 (200 OK):
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe"
  }
}
```

#### 프로필 조회
```http
GET /api/members/profile/
Authorization: Bearer <token>

응답 (200 OK):
{
  "id": 1,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe"
  },
  "bio": "Software Engineer",
  "favorite_categories": ["기술", "과학"],
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### 프로필 수정
```http
PATCH /api/members/profile/
Authorization: Bearer <token>
Content-Type: application/json

{
  "bio": "Senior Software Engineer",
  "favorite_categories": ["기술", "과학", "IT"]
}

응답 (200 OK):
{
  "id": 1,
  "bio": "Senior Software Engineer",
  "favorite_categories": ["기술", "과학", "IT"],
  "updated_at": "2024-01-02T12:00:00Z"
}
```

#### 로그아웃
```http
POST /api/members/logout/
Authorization: Bearer <token>

응답 (204 No Content):
```

---

### 기사 (News)

#### 기사 목록 조회
```http
GET /api/mynews/articles/?page=1&limit=20
Authorization: Bearer <token>

응답 (200 OK):
{
  "count": 1000,
  "next": "http://api.example.com/api/mynews/articles/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "url": "https://news.example.com/article1",
      "title": "Breaking: Major Tech Acquisition",
      "content": "...",
      "summary": "...",
      "category": "기술",
      "keywords": ["tech", "acquisition"],
      "sentiment": "positive",
      "published_at": "2024-01-01T10:00:00Z",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### 기사 검색
```http
GET /api/mynews/articles/search/?q=AI+기술&category=기술
Authorization: Bearer <token>

응답 (200 OK):
{
  "count": 45,
  "results": [...]
}
```

#### 기사 필터링
```http
GET /api/mynews/articles/?category=기술&sentiment=positive&limit=10
Authorization: Bearer <token>

응답 (200 OK):
{
  "count": 150,
  "results": [...]
}
```

#### 기사 상세 조회
```http
GET /api/mynews/articles/1/
Authorization: Bearer <token>

응답 (200 OK):
{
  "id": 1,
  "url": "https://news.example.com/article1",
  "title": "Breaking: Major Tech Acquisition",
  "content": "Full content...",
  "summary": "Summary...",
  "category": "기술",
  "keywords": ["tech", "acquisition"],
  "sentiment": "positive",
  "sentiment_score": 0.85,
  "published_at": "2024-01-01T10:00:00Z",
  "created_at": "2024-01-01T12:00:00Z",
  "sources": ["https://example.com"],
  "related_articles": [2, 3, 4]
}
```

#### 카테고리 목록
```http
GET /api/mynews/categories/
Authorization: Bearer <token>

응답 (200 OK):
[
  {
    "id": 1,
    "name": "기술",
    "description": "Technology news",
    "article_count": 250
  },
  {
    "id": 2,
    "name": "과학",
    "description": "Science news",
    "article_count": 180
  }
]
```

#### 키워드 추천
```http
GET /api/mynews/keywords/?q=AI
Authorization: Bearer <token>

응답 (200 OK):
[
  {
    "id": 1,
    "keyword": "AI",
    "frequency": 450,
    "trend": "upward"
  },
  {
    "id": 2,
    "keyword": "AI 윤리",
    "frequency": 230,
    "trend": "stable"
  }
]
```

---

## 🔐 인증 & 권한

### JWT 토큰 인증

```python
# settings.py 설정
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ]
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'ALGORITHM': 'HS256',
}
```

### API 요청 예시

```bash
# 토큰 포함 요청
curl -H "Authorization: Bearer <access_token>" \
     http://localhost:8000/api/members/profile/

# 토큰 갱신
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"refresh":"<refresh_token>"}' \
     http://localhost:8000/api/members/token/refresh/
```

### 권한 관리

```python
# views.py
from rest_framework.permissions import IsAuthenticated

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # 로그인한 사용자만 접근
        return Response(ProfileSerializer(request.user).data)
```

---

## 💾 데이터베이스 모델

### Member (사용자)

```python
# models.py
class Member(models.Model):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Profile(models.Model):
    user = models.OneToOneField(Member, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    favorite_categories = models.JSONField(default=list)
    avatar = models.ImageField(upload_to='avatars/', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Article (기사)

```python
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Keyword(models.Model):
    keyword = models.CharField(max_length=100, unique=True)
    frequency = models.IntegerField(default=0)
    trend = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

class Article(models.Model):
    url = models.URLField(unique=True)  # 중복 제거
    title = models.CharField(max_length=500)
    content = models.TextField()
    summary = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    keywords = models.ManyToManyField(Keyword)
    sentiment = models.CharField(max_length=20, choices=[
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ])
    sentiment_score = models.FloatField(default=0.0)
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['category', '-published_at']),
            models.Index(fields=['sentiment', '-created_at']),
        ]
```

---

## 🔄 API 응답 포맷

### 성공 응답 (200, 201)

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Article Title",
    ...
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 오류 응답 (400, 401, 404, 500)

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": {
      "email": ["Invalid email format"]
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## 🧪 테스트

### 유닛 테스트 실행

```bash
# 전체 테스트
python manage.py test

# 특정 앱 테스트
python manage.py test members
python manage.py test mynews

# 특정 테스트 클래스
python manage.py test members.tests.MemberViewTestCase

# 커버리지 보고서
coverage run --source='.' manage.py test
coverage report
coverage html
```

### 테스트 작성 예시

```python
# members/tests.py
from django.test import TestCase
from rest_framework.test import APIClient
from members.models import Member

class MemberViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.member = Member.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_login(self):
        response = self.client.post('/api/members/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)
```

---

## 📊 성능 최적화

### 1. 데이터베이스 최적화

```python
# select_related 사용 (외래키)
articles = Article.objects.select_related('category')

# prefetch_related 사용 (역참조)
articles = Article.objects.prefetch_related('keywords')

# only() - 필요한 필드만
articles = Article.objects.only('id', 'title', 'published_at')

# defer() - 특정 필드 제외
articles = Article.objects.defer('content')
```

### 2. 캐싱 설정

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50}
        }
    }
}

# views.py
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # 5분 캐싱
def category_list(request):
    categories = Category.objects.all()
    return Response(CategorySerializer(categories, many=True).data)
```

### 3. 페이지네이션

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# Custom 페이지네이션
class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100
```

### 4. 인덱싱

```python
# models.py
class Article(models.Model):
    ...
    class Meta:
        indexes = [
            models.Index(fields=['category', '-published_at']),
            models.Index(fields=['url']),
            models.Index(fields=['sentiment']),
        ]
```

---

## 🚀 배포

### Docker 배포

```dockerfile
# backend/Dockerfile.django
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 정적 파일 수집
RUN python manage.py collectstatic --noinput

# Gunicorn으로 실행
CMD ["gunicorn", "myproject.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--timeout", "60"]
```

### Docker Compose 설정

```yaml
# docker-compose.yml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.django
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/newsdb
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: python manage.py runserver 0.0.0.0:8000

  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: newsdb
      POSTGRES_USER: newsuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
```

---

## 🆘 트러블슈팅

### 1. 데이터베이스 연결 오류

```bash
# DB 연결 테스트
python backend/db_test.py

# 마이그레이션 상태 확인
python manage.py showmigrations

# 마이그레이션 롤백
python manage.py migrate mynews 0001
```

### 2. 정적 파일 404

```bash
# 정적 파일 수집
python manage.py collectstatic --noinput

# 개발 환경에서 정적 파일 서빙
python manage.py runserver --insecure
```

### 3. 느린 API 응답

```bash
# Django Debug Toolbar 설치
pip install django-debug-toolbar

# 쿼리 로깅
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
        },
    },
}
```

---

## 📚 추가 리소스

- Django 공식 문서: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- PostgreSQL 문서: https://www.postgresql.org/docs/

---

**마지막 업데이트:** 2026-01-02  
**버전:** 1.0  
**상태:** ✅ 프로덕션 준비 완료
