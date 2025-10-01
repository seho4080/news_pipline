# SSAFY PJT - Custom News Backend

**사용자 맞춤형 뉴스 추천 시스템을 위한 백엔드 서비스**

---

## 프로젝트 개요

본 프로젝트는 RSS 기반 뉴스 수집 데이터를 활용하여 사용자 관심사에 맞춘 뉴스 추천 기능을 제공하는 백엔드 시스템입니다.  
Django REST Framework 기반으로 API 서버를 구축하였습니다. 
웹서비스의 회원가입, 인증을 진행합니다. 
PostgreSQL과 pgvector를 활용한 벡터 기반 뉴스 유사도 추천, OPEN_AI API를 통해 한 챗봇, 대시보드 데이터 반환등의 기능을 합니다.

---

## 시작하기

### 1. 가상환경 설정

```bash
python3.10 -m venv ~/venvs/backend-pjt
source ~/venvs/backend-pjt/bin/activate
pip install -r requirements.txt
```

---

### 2. 마이그레이션 및 서버 실행

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

---


## 기술 스택

- Python 3.10
- Django
- PostgreSQL
- 인증: JWT
- OPEN AI

---

## 데이터베이스 설정

`myproject/settings.py` 내 `DATABASES` 설정은 아래와 같습니다:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "news",
        "USER": "ssafyuser",
        "PASSWORD": "ssafy",
        "HOST": "localhost",
        "PORT": 5432,
    }
}
```


## 주요 기능

### 1. 뉴스 목록 제공
- RSS를 통해 수집된 뉴스 데이터 제공
- 좋아요 기능

### 2. 개인화 대시보드
- 뉴스 소비 패턴 시각화
- 관심 분야 기반 트렌드 분석
- 직관적인 사용자 인터페이스 제공

### 3. 사용자 계정 관리
- 회원가입 및 로그인 기능
- 인증

### 4. 챗봇
- 사용자의 물음에 따라 질문 가능 
- 뉴스 기사에 대한 궁금한 점을 알 수 있음


---



## 참고용 API 명세
JWT를 안 쓴다면 "Authorization 헤더만 빠지고, 나머지 요청 형식(API URL, Method, Body, Response 등)은 동일하게 참고 가능

- 해당 레포지토리의 API_Sheet.pdf 참고
- 해당 레포지토리 상위 폴더 API_docs 참고
---

## 프로젝트 구조 예시

```
backend/
├── README.md
├── manage.py
├── mynews
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── enums.py
│   ├── mocking.py
│   ├── >migrations
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── members
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── >migrations
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── myproject
│   ├── __init__.py
│   ├── asgi.py
│   ├── response.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── requirements.txt
```
---
## 📦 앱별 기능 소개

### 📰 `mynews` 앱
뉴스 기사와 관련된 모든 기능을 담당합니다.

- 뉴스 기사 제공 및 관리
- 개별 기사에 대한 좋아요 기능
- 기사 읽음 기록 저장
- 기사 기반 추천 시스템 (비슷한 뉴스 추천)
- 기사에 대한 챗봇 응답 기능
- 기사별 댓글 기능
- 키워드 기반 뉴스 기사 검색

---

### 👤 `members` 앱
사용자 및 회원 관련 기능을 담당합니다.

- 회원가입 및 로그인 기능
- 사용자가 좋아요한 기사 목록 조회
- 사용자가 읽은 기사 목록 조회
- 사용자 맞춤형 대시보드 제공
- 사용자 기반 뉴스 검색 기능




---
# 코사인 유사도 기반 추천 시스템 정리

## ✅ 1. 사용자 좋아요 기반 추천

### 🔁 로직 흐름
1. **역참조(`likes__user`)**를 사용하여 해당 유저가 좋아요한 기사들을 조회한다.
2. 각 기사의 `embedding`을 가져와서 **벡터 평균**을 계산한다.
3. 모든 뉴스 기사와의 **코사인 유사도**를 계산한다.
4. **유사도가 높은 상위 5개 기사**를 추출하여 추천한다.

###  사용 기술 및 메서드
- Django ORM 역참조 (`likes__user`)
- `pgvector.django.VectorField`
- `CosineDistance` 또는 `embedding.l2_distance()` 등 pgvector 내장 함수
- Python에서 NumPy로 평균 임베딩 계산 및 유사도 필터링

###  반환 형식
```json
[
  {
    "article_id": 123,
    "title": "추천 기사 제목",
    "writer": "기자명",
    "write_date": "2025-04-25T14:30:00.000Z",
    "url": "https://example.com/news/123",
    "category": "IT_과학",
    "content": "...",
    "keywords": ["키워드1", "키워드2", "..."]
  }
]
```

---

## ✅ 2. 뉴스 내용 기반 추천

### 🔁 로직 흐름
1. 특정 기사의 `embedding` 값을 기준으로 한다.
2. 전체 뉴스 기사와의 **코사인 유사도**를 계산한다.
3. **자기 자신을 제외한** 상위 10개의 유사한 기사만 추출한다.

###  사용 기술
- 기준 기사: `news_article.objects.get(id=article_id)`
- `embedding.cosine_distance()` or `CosineDistance(embedding, ...)`
- 유사도 기준 정렬 및 필터링

###  반환 형식
```json
[
  {
    "article_id": 456,
    "title": "비슷한 뉴스 제목",
    "similarity": 0.92
  }
]
```
---

# 🤖 기사 기반 챗봇 기능

특정 뉴스 기사에 대해 사용자가 궁금한 점을 질문하면,  
기사 내용을 바탕으로 OpenAI GPT-4o 모델이 친절하게 답변을 제공하는 기능입니다.

---

### 🔁 로직 흐름

1. 사용자가 `/chatbot/<article_id>/` 엔드포인트로 질문을 보냅니다.
2. 요청한 사용자의 인증 여부를 확인합니다. (`IsAuthenticated`)
3. 해당 `article_id`에 해당하는 뉴스 기사를 조회합니다.
4. 기사 제목, 작성일, 본문을 포함한 초기 프롬프트를 생성합니다.
5. 이전 대화 기록이 있으면 세션을 통해 불러옵니다.
6. 최근 대화 내용(최대 20개)과 함께 GPT-4o 모델에 질의합니다.
7. GPT의 응답을 세션에 저장하고 클라이언트에 반환합니다.

---

### 🛠️ 사용 기술 및 도구

- Django REST Framework (`APIView`)
- 인증: `IsAuthenticated`, `request.user.is_authenticated`
- LangChain:
  - `ChatOpenAI`, `SystemMessage`, `HumanMessage`, `AIMessage`
  - `message_to_dict()`로 세션 저장
- OpenAI GPT-4o 모델
- Django 세션을 활용한 대화 지속 관리

---

### 📌 기능 특징

- 뉴스 기사 내용을 기반으로 자연어 질문에 응답
- 기사에 포함되지 않은 내용은 정중히 안내  
  (예: `"죄송해요, 여기 보고계신 기사에서는 찾을 수 없네요."`)
- 세션 기반 대화 히스토리 저장으로 이어지는 대화 가능
- 사용자 인증 기반 API (JWT 필요)

---

# 📊 사용자 대시보드 기능

사용자의 뉴스 소비 패턴을 집계하여 제공하는 개인화 대시보드 API입니다.  
좋아요한 기사, 읽은 날짜, 카테고리/키워드별 분포 등을 종합적으로 분석합니다.

---

### 🔁 로직 흐름

1. 현재 로그인한 사용자의 좋아요(`Likes`) 및 읽은 기록(`Reads`)을 조회
2. 좋아요한 뉴스 기사 목록을 기준으로:
   - **카테고리별 기사 수** 집계
   - **키워드별 기사 수** 집계 (JSON 파싱 포함)
3. 사용자의 뉴스 **읽은 날짜별 횟수** 집계
4. 사용자가 좋아요한 뉴스 기사 목록을 **요약 리스트 형태로 반환**

---

### 🛠️ 사용 기술 및 도구

- Django ORM (`Likes`, `Reads`, `news_article`)
- `select_related`를 통한 효율적 조회
- `defaultdict(int)`를 활용한 통계 집계
- `json.loads()`로 키워드 문자열 → 리스트 파싱
- 날짜 포맷: `read.read_at.strftime('%Y-%m-%d')`
- 커스텀 시리얼라이저: `DashboardArticleSerializer` 사용

---

### 📦 반환 예시

```json
{
  "message": "user1의 대시보드입니다",
  "category_count": {
    "IT_과학": 3,
    "정치": 2
  },
  "keyword_count": {
    "AI": 2,
    "기후변화": 1
  },
  "number_of_written_articles": {
    "2024-09-12": 3,
    "2024-09-13": 1
  },
  "favorite_articles": [
    {
      "id": 5,
      "title": "지속 가능한 에너지와 환경 보호",
      "author": "환경일보",
      "write_date": "2024-09-12"
    },
  ]
}

```
---

## ✨ 주요 기능 요약

- **좋아요 기반 추천**: 사용자의 선호도를 반영한 개인화 뉴스 추천
- **기사 내용 기반 추천**: 콘텐츠 임베딩을 활용한 유사 기사 추천
- **챗봇 기능**: 뉴스 기사에 대한 자연어 질의응답
- **대시보드 제공**: 사용자의 뉴스 소비 패턴 시각화 및 분석
- **검색기능 제공**: 찾고자 하는 뉴스를 검색
- 🎯 향후 확장 예정:
  - 키워드 유사도 기반 추천
  - 클릭 로그를 활용한 행동 기반 추천
