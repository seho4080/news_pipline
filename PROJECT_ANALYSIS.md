# 뉴스 파이프라인 프로젝트 구조 분석 보고서

> **작성일**: 2025-10-31  
> **프로젝트**: News Pipeline (실시간 뉴스 수집 및 분석 시스템)

---

## 📊 프로젝트 개요

마이크로서비스 아키텍처 기반의 실시간 뉴스 수집, 처리, 분석 및 제공 시스템으로, Kafka를 활용한 이벤트 기반 처리와 Elasticsearch를 통한 검색 기능, Airflow/Spark를 활용한 배치 처리를 갖춘 풀스택 애플리케이션입니다.

**핵심 기술 스택**:
- Backend: Django REST Framework + PostgreSQL (pgvector)
- Frontend: React + Vite
- Message Queue: Kafka + Zookeeper
- Search Engine: Elasticsearch
- Batch Processing: Apache Airflow + Apache Spark
- AI/ML: OpenAI API (GPT-4o-mini, text-embedding-3-small)
- Containerization: Docker + Docker Compose

---

## ✅ 잘한 점

### 1. **아키텍처 설계** ⭐⭐⭐⭐⭐

#### 마이크로서비스 분리
- **Producer-Consumer 패턴**: Kafka를 활용한 느슨한 결합 구조로 확장성 확보
- **관심사의 명확한 분리**: 수집(producer) → 전처리(consumer) → 저장(backend) → 분석(batch) → 제공(frontend)
- **독립적 배포 가능**: 각 서비스가 독립적인 Dockerfile 보유

#### 데이터 파이프라인 구조
```
RSS Feed → Producer (Kafka) → Consumer (전처리) → PostgreSQL/Elasticsearch
                                                        ↓
                                          Backend API ← Frontend
                                                        ↓
                                          Airflow/Spark (일간 리포트)
```

### 2. **Docker 컨테이너화** ⭐⭐⭐⭐⭐

#### 강점
- **완전한 환경 격리**: 모든 서비스가 컨테이너화되어 "내 컴퓨터에서는 되는데" 문제 해결
- **헬스체크 구현**: 모든 주요 서비스(postgres, kafka, elasticsearch, redis)에 헬스체크 설정
- **의존성 관리**: `depends_on` + `condition: service_healthy`로 올바른 시작 순서 보장
- **다중 환경 지원**: `docker-compose.yml`, `docker-compose.override.yml`, `docker-compose.prod.yml` 분리

```yaml
# 헬스체크 예시 (docker-compose.yml)
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-newsuser}"]
  interval: 30s
  timeout: 10s
  retries: 5
```

### 3. **에러 처리 및 로깅** ⭐⭐⭐⭐

#### Producer (`producer/produce.py`)
- **재시도 로직**: RSS 피드 가져오기와 크롤링에 지수 백오프 재시도 구현
- **상세한 로깅**: 파일 + 콘솔 동시 출력, 단계별 성공/실패 추적
- **DLQ(Dead Letter Queue)**: 실패한 메시지를 별도 토픽으로 분리

```python
# 지수 백오프 재시도 로직
for attempt in range(retries):
    try:
        # ... 작업 수행
        break
    except Exception as e:
        if attempt < retries - 1:
            time.sleep(2 ** attempt)  # 1초, 2초, 4초...
```

### 4. **AI 기반 전처리** ⭐⭐⭐⭐⭐

#### Consumer (`consumer/preprocess.py`)
- **토큰 제한 최적화**: tiktoken을 활용한 토큰 수 제한 (5000 토큰)으로 API 비용 절감
- **다양한 변환 기능**:
  - 키워드 추출 (GPT-4o-mini)
  - 카테고리 분류 (GPT-4o-mini)
  - 벡터 임베딩 (text-embedding-3-small)
- **Few-shot 프롬프팅**: 예시를 포함한 프롬프트로 정확도 향상

### 5. **데이터베이스 설계** ⭐⭐⭐⭐

#### PostgreSQL + pgvector
- **벡터 검색 지원**: pgvector 익스텐션으로 유사 뉴스 검색 가능
- **정규화된 스키마**: `news_article`, `Likes`, `Reads`, `Comment` 테이블 분리
- **하이브리드 스토리지**: PostgreSQL(트랜잭션) + Elasticsearch(검색) 조합

### 6. **배치 처리 시스템** ⭐⭐⭐⭐

#### Airflow + Spark
- **스케줄링**: 매일 새벽 1시 자동 리포트 생성 (`0 1 * * *`)
- **분산 처리**: Spark를 활용한 대용량 데이터 처리
- **데이터 아카이빙**: 처리 완료된 데이터 자동 이동
- **알림 기능**: 이메일로 리포트 전송

### 7. **문서화** ⭐⭐⭐

#### 다양한 문서 제공
- `docs/` 디렉토리 내 다수의 가이드 문서
- `README.md` 파일들 (프로젝트별)
- API 문서 (`api_docs/`) - Swagger/OpenAPI 스펙
- Docker 관련 가이드

---

## ⚠️ 모자란 점

### 1. **보안 취약점** ⚠️⚠️⚠️ (심각)

#### 하드코딩된 시크릿
```python
# backend/myproject/settings.py
SECRET_KEY = "django-insecure-k&tewfnqoy*i+o*9yw*!f)r02kz333fqnx99a(b)9xhg#-y8jh"
DEBUG = True  # 프로덕션에서도 True!
```

#### 데이터베이스 자격증명 노출
```python
DATABASES = {
    "default": {
        "USER": "ssafyuser",
        "PASSWORD": "ssafy",  # 평문 패스워드
        "HOST": "localhost",
    }
}
```

#### CORS 설정 과도하게 개방
```python
CORS_ALLOW_ALL_ORIGINS = True  # 모든 출처 허용
ALLOWED_HOSTS = ["*"]  # 모든 호스트 허용
```

### 2. **환경 변수 관리 부재** ⚠️⚠️⚠️

#### 문제점
- `.env` 파일이 `.gitignore`에 포함되지 않았을 가능성
- `.env.example` 파일들이 중복 (루트와 producer에 모두 존재)
- `settings.py`에서 환경 변수를 사용하지 않음
- Docker Compose에서는 환경 변수를 사용하지만 Django는 하드코딩

#### 개선 필요
```python
# 현재 (X)
SECRET_KEY = "django-insecure-..."

# 개선 (O)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret")
DEBUG = os.getenv("DEBUG", "False") == "True"
```

### 3. **코드 품질 이슈** ⚠️⚠️

#### 네이밍 컨벤션 불일치
```python
# models.py - 파이썬 컨벤션 위반
class news_article(models.Model):  # ❌ 소문자 + 언더스코어
    # 정석: class NewsArticle(models.Model):

class Likes(models.Model):  # ✅ 올바름
class Reads(models.Model):  # ✅ 올바름
```

#### 주석 처리된 코드
```python
# views.py
# def article_list(request):  # 사용하지 않는 코드를 주석 처리로 남김
# def article_detail(request, article_id):
```

#### 프록시 설정 주석
```python
# consumer/preprocess.py
os.environ.pop("HTTP_PROXY", None)  # 왜 필요한지 문서화 필요
os.environ.pop("HTTPS_PROXY", None)
# print("OPENAI KEY:", os.getenv("OPENAI_API_KEY"))  # 디버그 코드 제거 필요
```

### 4. **테스트 코드 부재** ⚠️⚠️⚠️

#### 현황
- `backend/mynews/tests.py` - 빈 파일
- `backend/members/tests.py` - 빈 파일
- 단위 테스트, 통합 테스트 없음
- CI/CD 파이프라인 없음

### 5. **에러 처리 개선 필요** ⚠️⚠️

#### Consumer의 에러 처리
```python
# consumer/preprocess.py
def transform_classify_category(self, content):
    # ...
    if model_output not in self.categories:
        model_output = "미분류"  # ✅ 폴백 처리
    return model_output
```

**개선 필요 사항**:
- OpenAI API 호출 실패 시 처리 부재
- 네트워크 타임아웃 처리 부족
- 데이터베이스 연결 실패 시 복구 로직 없음

### 6. **모니터링 및 관찰성 부족** ⚠️⚠️

#### 누락된 기능
- **메트릭 수집**: Prometheus/Grafana 없음
- **분산 추적**: Jaeger/Zipkin 없음
- **중앙 로깅**: ELK Stack/Loki 없음
- **알림 시스템**: Kafka lag, DB 연결 실패 등 알림 없음

### 7. **성능 최적화 미흡** ⚠️

#### 데이터베이스
```python
# 인덱스 누락 가능성
class news_article(models.Model):
    category = models.CharField(max_length=25)  # 인덱스 필요
    write_date = models.DateTimeField()  # 인덱스 필요
    # db_index=True 누락
```

#### API 페이지네이션
- `views.py`에서 페이지네이션 설정 확인 필요
- 대량 데이터 조회 시 성능 저하 가능성

### 8. **문서화 개선 필요** ⚠️

#### 문제점
- `docs/` 디렉토리에 중복 README 파일 (README.md, README1.md, total_readme.md)
- API 문서와 실제 코드 동기화 상태 불명확
- 아키텍처 다이어그램 부재
- 배포 가이드 부족

---

## 🔧 고쳐야 할 점 (우선순위별)

### 🔴 긴급 (즉시 수정 필요)

#### 1. 보안 설정 수정

**settings.py 환경 변수화**
```python
# backend/myproject/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY 환경 변수가 설정되지 않았습니다.")

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "news"),
        "USER": os.getenv("DB_USER", "ssafyuser"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": int(os.getenv("DB_PORT", "5432")),
    }
}
```

**CORS 설정 제한**
```python
# 개발 환경
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
    ]
```

#### 2. .gitignore 업데이트

**추가해야 할 항목**
```gitignore
# 환경 변수
.env
.env.local
.env.*.local

# 데이터베이스
*.db
*.sqlite3
db.sqlite3

# 로그 파일
*.log
logs/
*.log.*

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Docker
.dockerignore

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Airflow
airflow-webserver.pid
airflow-scheduler.pid
```

#### 3. 민감 정보 제거 및 .env 파일 생성

**.env.example (루트)**
```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=newsdb
POSTGRES_USER=newsuser
POSTGRES_PASSWORD=your-password-here
DB_HOST=postgres
DB_PORT=5432

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=news-raw
DLQ_TOPIC=news-dlq

# OpenAI
OPENAI_API_KEY=your-openai-api-key-here

# Elasticsearch
ELASTICSEARCH_HOST=elasticsearch:9200

# Redis
REDIS_URL=redis://redis:6379/0

# RSS Producer
RSS_FETCH_INTERVAL=300
MAX_RETRIES=3
REQUEST_TIMEOUT=30
```

### 🟡 중요 (1-2주 내 수정)

#### 4. 코드 품질 개선

**모델 네이밍 수정**
```python
# backend/mynews/models.py

# Before (X)
class news_article(models.Model):
    pass

# After (O)
class NewsArticle(models.Model):
    class Meta:
        db_table = 'news_article'  # DB 테이블명 유지
        verbose_name = '뉴스 기사'
        verbose_name_plural = '뉴스 기사들'
        indexes = [
            models.Index(fields=['category', '-write_date']),
            models.Index(fields=['write_date']),
        ]
```

**주석 처리된 코드 제거**
```python
# views.py - 사용하지 않는 함수는 삭제
# def article_list(request):  # ❌ 삭제
#     ...

# Git 히스토리에 남아있으므로 안심하고 삭제 가능
```

#### 5. 에러 처리 강화

**OpenAI API 호출 래퍼**
```python
# consumer/preprocess.py

from tenacity import retry, stop_after_attempt, wait_exponential

class Preprocess:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _call_openai_api(self, messages, max_tokens=100):
        """OpenAI API 호출 (재시도 포함)"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=max_tokens,
                timeout=30.0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API 호출 실패: {e}")
            raise

    def transform_extract_keywords(self, text):
        """키워드 추출 (에러 처리 개선)"""
        try:
            text = self.preprocess_content(text)
            if not text or text == "본문 없음":
                return "키워드 없음"
            
            # ... 기존 로직 ...
            
        except Exception as e:
            logger.error(f"키워드 추출 실패: {e}")
            return "키워드 추출 실패"
```

#### 6. 데이터베이스 최적화

**인덱스 추가**
```python
# backend/mynews/models.py

class NewsArticle(models.Model):
    # ... 기존 필드 ...
    
    class Meta:
        indexes = [
            models.Index(fields=['category', '-write_date']),
            models.Index(fields=['write_date']),
            models.Index(fields=['author']),
        ]
```

**Connection Pooling 설정**
```python
# backend/myproject/settings.py

DATABASES = {
    "default": {
        # ... 기존 설정 ...
        'CONN_MAX_AGE': 600,  # 연결 재사용 (10분)
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

### 🟢 개선 (시간 있을 때)

#### 7. 테스트 코드 작성

**단위 테스트 예시**
```python
# backend/mynews/tests.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import NewsArticle, Likes

User = get_user_model()

class NewsArticleModelTest(TestCase):
    def setUp(self):
        self.article = NewsArticle.objects.create(
            title="테스트 기사",
            content="테스트 내용",
            category="경제",
            url="http://example.com/test"
        )
    
    def test_article_creation(self):
        """기사 생성 테스트"""
        self.assertEqual(self.article.title, "테스트 기사")
        self.assertEqual(self.article.category, "경제")
    
    def test_article_str(self):
        """기사 문자열 표현 테스트"""
        self.assertEqual(str(self.article), "테스트 기사")

class LikesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123"
        )
        self.article = NewsArticle.objects.create(
            title="테스트",
            content="내용",
            category="정치"
        )
    
    def test_like_creation(self):
        """좋아요 생성 테스트"""
        like = Likes.objects.create(
            user=self.user,
            article=self.article
        )
        self.assertEqual(Likes.objects.count(), 1)
```

#### 8. API 문서 자동화

**drf-spectacular 도입**
```python
# requirements.txt에 추가
drf-spectacular==0.27.0

# settings.py
INSTALLED_APPS = [
    # ...
    'drf_spectacular',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'News Pipeline API',
    'DESCRIPTION': '뉴스 수집 및 분석 API',
    'VERSION': '1.0.0',
}

# urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

#### 9. 모니터링 시스템 구축

**Prometheus + Grafana 추가**
```yaml
# docker-compose.monitoring.yml

version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - news-network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    networks:
      - news-network

volumes:
  prometheus_data:
  grafana_data:
```

#### 10. CI/CD 파이프라인 구축

**GitHub Actions 예시**
```yaml
# .github/workflows/ci.yml

name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_newsdb
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      working-directory: ./backend
      run: |
        pip install -r requirements.txt
    
    - name: Run migrations
      working-directory: ./backend
      env:
        DATABASE_URL: postgres://test_user:test_pass@localhost:5432/test_newsdb
      run: |
        python manage.py migrate
    
    - name: Run tests
      working-directory: ./backend
      run: |
        python manage.py test
    
    - name: Lint with flake8
      working-directory: ./backend
      run: |
        pip install flake8
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

  test-frontend:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      working-directory: ./frontend-react
      run: npm ci
    
    - name: Run lint
      working-directory: ./frontend-react
      run: npm run lint
    
    - name: Build
      working-directory: ./frontend-react
      run: npm run build
```

---

## 📋 체크리스트

### 즉시 수행 (1-3일)
- [ ] `settings.py`에서 하드코딩된 SECRET_KEY 제거 및 환경 변수화
- [ ] `.env.example` 파일 생성 및 `.gitignore`에 `.env` 추가
- [ ] `DEBUG=False` 및 `ALLOWED_HOSTS` 제한 (프로덕션)
- [ ] 데이터베이스 자격증명을 환경 변수로 이동
- [ ] CORS 설정 제한

### 단기 (1-2주)
- [ ] `news_article` 모델명을 `NewsArticle`로 변경
- [ ] 주석 처리된 코드 제거
- [ ] 데이터베이스 인덱스 추가
- [ ] OpenAI API 호출에 재시도 로직 추가
- [ ] 로깅 레벨 및 포맷 표준화

### 중기 (1개월)
- [ ] 단위 테스트 작성 (최소 70% 커버리지)
- [ ] API 문서 자동화 (drf-spectacular)
- [ ] CI/CD 파이프라인 구축 (GitHub Actions)
- [ ] 모니터링 시스템 구축 (Prometheus + Grafana)
- [ ] 문서 정리 및 통합 (중복 README 제거)

### 장기 (3개월)
- [ ] 부하 테스트 및 성능 최적화
- [ ] 캐싱 전략 구현 (Redis 활용)
- [ ] Rate Limiting 구현
- [ ] 백업 및 재해 복구 계획 수립
- [ ] 로그 중앙화 (ELK Stack)

---

## 🎯 권장 아키텍처 개선 방향

### 현재 아키텍처의 강점 유지
1. ✅ Kafka 기반 이벤트 스트리밍
2. ✅ Docker Compose를 활용한 로컬 개발 환경
3. ✅ PostgreSQL + Elasticsearch 하이브리드 스토리지
4. ✅ Airflow/Spark 배치 처리

### 제안하는 개선 사항

#### 1. API Gateway 도입
```
Frontend → Nginx (API Gateway) → Backend Services
                                → Elasticsearch (직접 접근 금지)
```

#### 2. 서비스 메시 고려 (선택)
- Istio 또는 Linkerd 도입 검토
- 서비스 간 통신 암호화
- 트래픽 관리 및 카나리 배포

#### 3. 데이터베이스 샤딩 준비
```python
# 향후 대량 데이터 처리를 위한 파티셔닝
class NewsArticle(models.Model):
    # ...
    class Meta:
        db_table = 'news_article'
        # PostgreSQL 파티셔닝 (날짜별)
        # CREATE TABLE news_article_2024_01 PARTITION OF news_article
        # FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

#### 4. 캐싱 레이어 강화
```python
# Django Cache Framework 활용
from django.core.cache import cache

def get_popular_articles(category=None):
    cache_key = f"popular_articles_{category}"
    articles = cache.get(cache_key)
    
    if articles is None:
        articles = NewsArticle.objects.filter(
            category=category
        ).order_by('-total_likes')[:10]
        cache.set(cache_key, articles, 300)  # 5분 캐싱
    
    return articles
```

---

## 💡 최종 평가

### 종합 점수: **75/100** (B+)

| 항목 | 점수 | 평가 |
|-----|-----|-----|
| 아키텍처 설계 | 90/100 | 마이크로서비스, 이벤트 기반 처리 등 현대적 설계 |
| 코드 품질 | 65/100 | 네이밍 불일치, 주석 코드, 테스트 부재 |
| 보안 | 50/100 | 하드코딩된 시크릿, 과도한 권한 설정 |
| 성능 | 70/100 | 인덱스 부족, 캐싱 미흡 |
| 모니터링 | 60/100 | 로깅은 있으나 메트릭/추적 부재 |
| 문서화 | 75/100 | 다양한 문서 있으나 중복 및 동기화 문제 |
| 확장성 | 85/100 | Kafka, Docker로 확장 가능 구조 |
| 유지보수성 | 70/100 | 컨테이너화로 관리 용이하나 테스트 부족 |

### 강점 요약
1. 🏆 **현대적인 기술 스택**: Kafka, Elasticsearch, Airflow/Spark 활용
2. 🏆 **마이크로서비스 아키텍처**: 느슨한 결합과 높은 확장성
3. 🏆 **완전한 컨테이너화**: Docker Compose로 일관된 환경
4. 🏆 **AI 통합**: OpenAI API를 활용한 지능형 처리

### 개선 필요 영역
1. 🔴 **보안 강화**: 환경 변수 관리, 권한 제한
2. 🔴 **코드 품질**: 네이밍, 주석, 테스트
3. 🟡 **모니터링**: 메트릭 수집, 알림 시스템
4. 🟡 **성능 최적화**: 인덱스, 캐싱, 쿼리 최적화

---

## 📚 참고 자료

### 보안
- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

### 테스팅
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [pytest-django](https://pytest-django.readthedocs.io/)

### 모니터링
- [Prometheus Django Exporter](https://github.com/korfuri/django-prometheus)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)

### 성능
- [Django Database Optimization](https://docs.djangoproject.com/en/stable/topics/db/optimization/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)

---

**작성자 노트**: 이 프로젝트는 기술적으로 매우 잘 설계된 시스템입니다. 보안과 코드 품질 부분만 개선하면 프로덕션 수준의 애플리케이션이 될 수 있습니다. 특히 긴급 항목(보안)은 즉시 수정하고, 중요 항목(테스트, 모니터링)은 단계적으로 적용하시기 바랍니다.
