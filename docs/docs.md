## 전체 파일구조
```
project-root/
├── api_docs/
│ └── ... (API명세, ERD)
│
├── backend/
│ └── ... (Django 백엔드 구성)
│
├── batch/
│ └── ... (Airflow 등 배치 스크립트)
│
├── consumer/
│ └── ... (Spark Consumer 관련 코드)
│
├── data/
│ └── ... (수집 데이터, 중간 저장 파일)
│
├── frontend/
│ └── ... (react 프론트엔드 코드)
│
├── producer/
│ └── ... (Kafka Producer, 뉴스 수집 스크립트)
│
├── elastic_search/
│ └── ... (엘라스틱서치 관련 설정)
│
├── .env
├── README.md
└── requirements.txt
```
## 데이터 흐름
```
(docker) (docker)            (airflow)
KAFKA -> SPARK -> POSTGRESQL -> SPARK           -> DJANGO(API) -> REACT -> CLIENT
                             -> ELASTIC SEARCH 
```
## 시스템 구성 요소 설명

| 구성 요소            | 설명                                                  |
|---------------------|-------------------------------------------------------|
| **Kafka → SPARK**   | 뉴스 수집 및 실시간 처리                              |
| **SPARK → PostgreSQL** | 정형 DB에 저장 및 갱신 처리                         |
| **SPARK → Elasticsearch** | 검색용 저장소로 즉시 반영                        |
| **Airflow**         | (예시: 10분) 배치 형태로 주기적 데이터 정합성 보완   |
| **Django API**      | 검색 기능 REST API 제공                               |
| **REACT**          | 사용자 검색 UI 제공                                   |
| **Kibana**          | 검색 트렌드 등 시각화를 통한 모니터링 및 분석         |

<details>
<summary>DB</summary>

## DB 테이블 

### 뉴스 기사 테이블
```
CREATE TABLE news_article (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    writer VARCHAR(255) NOT NULL,
    write_date TIMESTAMP NOT NULL,
    category VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    url VARCHAR(200) UNIQUE NOT NULL,
    keywords VARCHAR(100),              -- 핵심키워드 5개 추출
    embedding VECTOR(1536) NOT NULL,    -- 단어 임베딩
    updated_at TIMESTAMP DEFAULT now()  -- 갱신 시점 자동 기록을 위한 추가 컬럼
);
```
### 좋아요 테이블 
```
CREATE TABLE likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES members_user(id) ON DELETE CASCADE,
    article_id TEXT NOT NULL REFERENCES news_article(url) ON DELETE CASCADE,
    UNIQUE (user_id, article_id)
);
```
### 읽음 여부 테이블 
```
CREATE TABLE read (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES members_user(id) ON DELETE CASCADE,
    article_id TEXT NOT NULL REFERENCES news_article(url) ON DELETE CASCADE,
    read_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```
### USER 테이블 django AbstractUser 상속
```
CREATE TABLE members_user (
    id SERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP NULL,
    is_superuser BOOLEAN NOT NULL,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    is_staff BOOLEAN NOT NULL,
    is_active BOOLEAN NOT NULL,
    date_joined TIMESTAMP NOT NULL,
    -- 필요 시 추가할 사용자 정의 필드들 예시
    -- nickname VARCHAR(100),
    UNIQUE (username)
);
```

![ERD 다이어그램](./api_docs/ERD.png)
### 그 외 인증관련 tables
</details>


<details>
<summary>backend</summary>


**사용자 맞춤형 뉴스 추천 시스템을 위한 백엔드 서비스**

---

## 프로젝트 개요
### SSAFY PJT - Custom News Backend

본 프로젝트는 RSS 기반 뉴스 수집 데이터를 활용하여 사용자 관심사에 맞춘 뉴스 추천 기능을 제공하는 백엔드 시스템입니다.  
Django REST Framework 기반으로 API 서버를 구축하였으며 이후, PostgreSQL과 pgvector를 활용한 벡터 기반 뉴스 유사도 추천 기능을 포함하게 됩니다.

---

## 시작하기

### 1. 가상환경 설정

```bash
python3.10 -m venv ~/venvs/backend-pjt
source ~/venvs/backend-pjt/bin/activate
pip install -r requirements.txt
```

---

### 2. Django 설정

`myproject/settings.py` 내 `DATABASES` 설정

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

---

### 3. 마이그레이션 및 서버 실행

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

---


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


---

## 참고용 API 명세
JWT를 안 쓴다면 "Authorization 헤더만 빠지고, 나머지 요청 형식(API URL, Method, Body, Response 등)은 동일하게 참고 가능

- 해당 레포지토리의 API_Sheet.pdf 참고

---

## 프로젝트 구조 예시

```
├── manage.py
├── README.md
├── requirements.txt
├── API_Sheet.pdf
├── db_test.py
├── members/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│       └── __init__.py
├── mynews/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── enums.py
│   ├── mocking.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│       └── __init__.py
├── myproject/
│   ├── __init__.py
│   ├── asgi.py
│   ├── response.py
│   ├── serializers.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
```
---

# url 기준 기능 설명 

/api/members/signup/             # 회원가입
<summary>🟢 [POST] /api/members/signup/ - 회원가입</summary>

## ✅ 기능 설명
회원 가입을 처리하는 API입니다.

### 📥 요청

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| username | string | ✅ | 유저 ID |
| password | string | ✅ | 비밀번호 |
| email    | string | ✅ | 이메일 주소 |

요청 예시:
```json
{
  "username": "ssafy123",
  "password": "secure123!",
  "email": "ssafy@example.com"
}
{
  "message": "회원가입이 완료되었습니다."
}


/api/members/me/                # 내 정보 조회
/api/members/login/            # JWT 로그인 (토큰 발급)
/api/members/likes/            # 내가 좋아요한 기사 목록
/api/members/reads/            # 내가 읽은 기사 목록
/api/members/recommendations/ # 키워드 기반 추천
/api/members/dashboard/       # 유저 맞춤 대시보드

/api/news/                        # 전체 기사 목록
/api/news/<int:article_id>/       # 기사 상세 조회
/api/news/<int:article_id>/likes/ # 좋아요 토글
/api/news/<int:article_id>/similar # 유사 기사 추천
/api/news/search/?q=키워드        # 뉴스 검색



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
## ✨ 완성된 기능 요약
-  **좋아요 기반 추천**: 개인화 추천
-  **기사 내용 기반 추천**: 컨텐츠 기반 추천
-  코사인 유사도를 기반으로 유사한 뉴스 추천 가능
- 🎯 향후에는 키워드 유사도, 클릭 로그 기반 추천 등 확장 가능


---

## 기술 스택

- Python 3.10
- Django
- PostgreSQL
- 인증: JWT(해당 코드 기준)


</details>

<details>
<summary>producer</summary>

## produce.py
---
### 함수 기능 요약

- `fetch_rss(url)`: RSS 피드를 파싱해 최신 뉴스 리스트를 가져옵니다.
- `crawl_article(url)`: 뉴스 본문 HTML을 크롤링해 텍스트로 정제합니다.
- `enrich_article(entry, category)`: RSS entry에 본문을 추가하여 구조화된 dict 반환
```
{
        'title': entry.title,
        'write_date': entry.published,
        'content': content,
        'url': entry.link,                  #  'url' 필드로 맞춤
}
```
- `main()`: 각 카테고리별 뉴스 수집 및 Kafka로 전송하는 전체 파이프라인 수행
- Json 형식으로 consumer에게 send


> 후에 .env 파일에서 KAFKA_BROKER, TOPIC 설정을 따로 할 수 있을 것임.
</details>


<details>
<summary>consumer</summary>

- flink


</details>


<details>
<summary>front</summary>



</details>


<details>
<summary>api_docs</summary>



</details>

<details>
<summary>ELASTIC SEARCH</summary>

### elastic_search.py
- 검색 위한 elastic search
- 이 파일은 인덱스 생성 및 설정하는 파일입니다. 

- mapping
```
    "mappings": {
        "properties": {
            "title":     { "type": "text" },     #// 검색 대상
            "content":   { "type": "text" },     #// 검색 대상
            "writer":    { "type": "text" },     #// 검색 대상
            "category":  { "type": "keyword" },  #// 필터링용
            "url":       {"type": "text"},       # 중복 확인이나 보여주기 용도
            "keywords":  { "type": "keyword" },  #// 필터/정렬용
            "write_date":{ "type": "date" },      #// 정렬 및 기간 필터
            "updated_at":{ "type": "date" }     # 생성시기
        }
    },
```
- setting
```
    "settings":{
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "korean_analyzer": {
                    "type": "custom",
                    "tokenizer": "nori_tokenizer"
                }
            }
        }
    }
```

### flink_es.py

#### 🧩 구성 요소

```
Kafka → Flink → *PostgreSQL + *Elasticsearch  (실시간 저장)
                           ↓
                    *[Airflow DAG]
                   (cron 기반 주기 동기화)
                           ↓
                   *Elasticsearch 재동기화
```

1. **Flink가 Kafka 메시지 소비 및 처리**  
   - 뉴스 전처리 (임베딩, 키워드 추출 등)
   - PostgreSQL에 저장 (트랜잭션 기반)
   - ES에 저장 (PG 성공 시에만 전송)

2. **Airflow DAG이 주기적으로 동기화**  
   - `updated_at` 기준으로 최근 변경된 문서만 Elasticsearch로 전송
   - 실시간 처리 실패 시 보완 목적

/batch/dags/psql_es_synchronization.py
## ✅ 동기화 DAG 주요 기능

- 주기: 매 5분 or 매 1시간
- 기준: `updated_at > last_sync_time`
- 처리: URL 기반 문서 ID 사용 (`quote(url)`)
- 보장: ES 일부 누락/실패 복구 가능

---

## 💡 운영 팁

- `keywords`, `embedding` 등도 함께 전달하여 검색/추천 기반 구축
- 삭제 동기화는 별도 로그 테이블 사용 권장
- `LIMIT` + 반복 페이징 처리로 대량 데이터 대응
- `last_sync_time`은 파일, DB, Redis 등으로 관리


</details>