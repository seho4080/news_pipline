# 📰 SSAFY News Platform

> **AI 기반 맞춤형 뉴스 추천 시스템** - 실시간 뉴스 수집부터 개인화 추천까지

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2.20-green.svg)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org)
[![Docker](https://img.shields.io/badge/Docker-Latest-blue.svg)](https://docker.com)

---

## 🚀 빠른 시작

### Docker 방식 (권장)
```bash
# 1. 환경 설정
cp .env.example .env
# .env 파일에서 OpenAI API 키 등 설정

# 2. 서비스 시작
./docker/scripts/setup.sh
./docker/scripts/build.sh
./docker/scripts/deploy.sh start

# 3. 서비스 접속
# Frontend: http://localhost
# Backend API: http://localhost/api
# Django Admin: http://localhost/admin
```

### 개발 환경 설정
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver

# Frontend
cd frontend
npm install
npm run dev
```

---

## 📁 프로젝트 구조

```
data-pjt-seho-jungrae/
├── 📱 frontend/          # React 프론트엔드
├── 🖥️ backend/           # Django 백엔드
├── 📡 producer/          # Kafka Producer (RSS 크롤러)
├── ⚙️ consumer/          # Kafka Consumer (AI 전처리)
├── 🗓️ batch/             # Airflow + Spark 배치
├── 🐳 docker/            # Docker 설정
├── 🔍 search/            # 검색 엔진 설정
├── 🔧 scripts/           # 유틸리티 스크립트
├── ⚙️ config/            # 설정 파일 모음
├── 📚 docs/              # 문서 모음
└── 📋 api_docs/          # API 문서 및 ERD
```

---

## 🌟 주요 기능

- **🤖 AI 기반 개인화 추천**: pgvector 코사인 유사도 활용
- **⚡ 실시간 뉴스 수집**: Kafka + RSS 크롤링
- **🔍 지능형 검색**: Elasticsearch 기반 전문 검색
- **💬 AI 챗봇**: OpenAI GPT-4 질의응답
- **📊 개인화 대시보드**: 사용자 뉴스 소비 패턴 분석

---

## 🛠️ 기술 스택

### Frontend
**React 18** + Vite + Chart.js + Axios + SCSS

### Backend  
**Django 4.2.20** + DRF + PostgreSQL + pgvector + Redis

### Data Pipeline
**Apache Kafka** + Elasticsearch + Airflow + Spark

### Infrastructure
**Docker Compose** + Nginx + Gunicorn

---

## 📖 문서

- **📋 [종합 가이드](total_readme.md)**: 프로젝트 전체 상세 설명
- **🔧 [실행 가이드](docs/실행가이드.md)**: 개발 환경 설정
- **🏗️ [Docker 가이드](docker/README.md)**: 컨테이너 배포 방법
- **📊 [API 문서](api_docs/)**: REST API 명세서

---

## 🧪 테스트 및 개발

```bash
# 서비스 상태 확인
./docker/scripts/deploy.sh status

# 실시간 모니터링
./docker/scripts/monitor.sh monitor

# 특정 서비스 로그 확인
./docker/scripts/monitor.sh logs backend

# 테스트 스크립트 실행
cd scripts
python extract_pgvector_test.py
```

---

## 🔧 운영 및 관리

```bash
# 서비스 재시작
./docker/scripts/deploy.sh restart

# 데이터 백업
./docker/scripts/deploy.sh backup

# 성능 모니터링
./docker/scripts/monitor.sh performance
```

---

## 📞 지원

- **🐛 이슈 리포팅**: GitHub Issues
- **📚 문서**: `docs/` 디렉토리 참조
- **🔧 트러블슈팅**: `docker/README.md` 참조

---

<div align="center">

**🏆 SSAFY 11기 관통프로젝트 🏆**

*AI 기반 맞춤형 뉴스 추천 시스템*

[![SSAFY](https://img.shields.io/badge/SSAFY-11th-blue)](https://ssafy.com)

</div>
```
project-root/
│
├── backend/
│ └── ... (Django 백엔드 구성)
│
├── batch/
│ └── ... (Airflow 등 배치 스크립트)
│
├── consumer/
│ └── ... (Kafka/Flink Consumer 관련 코드)
││
├── frontend/
│ └── ... (Vue.js 프론트엔드 코드)
│
├── producer/
│ └── ... (Kafka Producer, 뉴스 수집 스크립트)
│
│
├── .env
├── README.md
└── requirements.txt

```
## 데이터 흐름
```
(docker) (docker)            (airflow)
KAFKA -> FLINK -> POSTGRESQL -> SPARK           -> DJANGO(API) -> VUE -> CLIENT
                             -> ELASTIC SEARCH 
```
## 시스템 구성 요소 설명

| 구성 요소            | 설명                                                  |
|---------------------|-------------------------------------------------------|
| **Kafka → Flink**   | 뉴스 수집 및 실시간 처리                              |
| **Flink → PostgreSQL** | 정형 DB에 저장 및 갱신 처리                         |
| **Flink → Elasticsearch** | 검색용 저장소로 즉시 반영                        |
| **Airflow**         | (예시: 10분) 배치 형태로 주기적 데이터 정합성 보완   |
| **Django API**      | 검색 기능 REST API 제공                               |
| **Vue.js**          | 사용자 검색 UI 제공                                   |
| **Kibana**          | 검색 트렌드 등 시각화를 통한 모니터링 및 분석         |

<details>
<summary>DB_schema</summary>
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
<summary>Django</summary>
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


</details>

<details>
<summary>Produce</summary>

# 📰 Producer

연합뉴스 RSS 피드에서 뉴스 데이터를 수집하고, 본문 내용을 크롤링하여 Kafka로 전송하는 뉴스 프로듀서입니다.

---

## ✅ 주요 기능

- 연합뉴스의 다양한 카테고리(RSS 피드)에서 뉴스 수집
- 뉴스 기사 본문을 크롤링하여 콘텐츠 보강
- Kafka 토픽으로 실시간 데이터 전송 (`news-topic`)
- 기사 제목, 작성일, 본문, URL 정보를 JSON 형태로 전송

---

## 📦 사용 라이브러리

- `feedparser`: RSS 파싱
- `BeautifulSoup`: HTML 본문 크롤링
- `requests`, `urllib.request`: 웹 요청 처리
- `kafka-python`: Kafka 메시지 전송
- `json`, `time`, `ssl`: 유틸

---

## 🛠️ 설정값

- **Kafka 브로커 주소**: `localhost:9092`  
  → 필요 시 환경 변수 또는 `.env`로 분리 추천
- **Kafka 토픽 이름**: `news-topic`

---

## 🧪 실행 방법
kafka 실행    
1. Zookeeper 실행

    ```bash
    $KAFKA_HOME/bin/zookeeper-server-start.sh $KAFKA_HOME/config/zookeeper.properties
    ```

2. Kafka 브로커 실행

    ```bash
    $KAFKA_HOME/bin/kafka-server-start.sh $KAFKA_HOME/config/server.properties
    ```
    
3. topic 생성

    ```bash
    $KAFKA_HOME/bin/kafka-topics.sh --create \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 1 \
    --topic news-topic
    ```

4. produce.py실행
```bash
# Kafka 서버가 실행 중이어야 함
python produce.py
```

---

## 발전 방향

### ✅ 1. 수집 대상 확장
- 연합뉴스 외 **다양한 언론사 RSS 피드 추가**
- 포털 뉴스(네이버, 다음 등) 기반 크롤링 기능 연동
- 해외 뉴스(RSS 또는 API) 추가하여 **다국어 뉴스 수집**

### ✅ 2. Kafka 연동 개선
- **에러 핸들링 및 재전송 로직** 구현 (retry, dead-letter queue 등)
- 전송 성공/실패 **로깅 및 메트릭 수집**
- Kafka 토픽을 **카테고리별로 분리**하여 처리 유연성 증가


### ✅ 3. 스케줄링 자동화
- 현재는 수동 실행 → **Airflow, Cron 등으로 자동화**
- **주기별로 수집된 뉴스 내역 로그화 및 저장**

### ✅ 4. 데이터 유효성 검사 강화
- 기사 본문의 길이, 구조를 기반으로 **불완전한 뉴스 제거**
- `produce.py` 내에서 **제목/본문/URL 누락 여부 체크 후 Kafka 전송 필터링**
- 중복 제거는 `consumer` 또는 저장 단계에서 **DB 기준 비교 후 처리**


## 함수 기능 요약

- `fetch_rss(url)`: RSS 피드를 파싱해 최신 뉴스 리스트를 가져옵니다.
- `crawl_article(url)`: 뉴스 본문 HTML을 크롤링해 텍스트로 정제합니다.
- `enrich_article(entry, category)`: RSS entry에 본문을 추가하여 구조화된 dict 반환
- `main()`: 각 카테고리별 뉴스 수집 및 Kafka로 전송하는 전체 파이프라인 수행


</details>


<details>
<summary>Consume</summary>
# 🔄 Kafka Consumer - Flink Stream 처리

Kafka로 수신된 뉴스 데이터를 PostgreSQL, Elasticsearch, HDFS에 순차적으로 저장하는 실시간 Consumer 처리 흐름입니다.

---

## ✅ 주요 흐름

1. Kafka에서 뉴스 데이터를 수신 (`news-topic`)
2. 뉴스 본문 전처리 (내용 정제, 기자명 추출, 키워드/카테고리 분류, 임베딩 생성)
3. PostgreSQL DB에 기사 저장 (중복 URL 무시)
4. Elasticsearch 색인 생성 (검색 가능성 확보)
5. HDFS에 JSON 파일 저장 (날짜별 디렉토리)

---

## 🛠 사용 기술 스택

- **Apache Flink (PyFlink)**: 스트리밍 데이터 처리
- **Kafka**: 뉴스 데이터 소비
- **PostgreSQL**: 정형 데이터 저장
- **Elasticsearch**: 뉴스 검색 색인
- **HDFS**: 장기 보관용 JSON 데이터 저장
- **LangChain / OpenAI** 기반 전처리 (`Preprocess` 클래스)

---

## 🔁 처리 로직 상세

### PgThenEs (MapFunction)

- `title`, `content`, `url`, `write_date` 등의 필드를 파싱
- `Preprocess` 클래스로 전처리 수행:
  - 본문 정제
  - 기자명 추출 (ex. `홍길동 기자`)
  - 키워드 추출 (`extract_keywords`)
  - 카테고리 분류 (`classify_category`)
  - 임베딩 생성 (`transform_to_embedding`)
- **중복 URL**은 PostgreSQL에서 무시
- Elasticsearch 색인 문서 생성 및 URL 기반 doc_id 설정
- HDFS에는 날짜 기준 디렉토리로 JSON 저장

---

## 📂 HDFS 저장 경로 예시
/user/hadoop/news/2025/05/27/news_153245_812374.json


---

## ⚠️ 예외 처리

- PG 중복 URL → 삽입 안 됨 (로그 출력)
- ES 오류 → 상태 코드 및 응답 로그
- HDFS 저장 실패 → 오류 로그 출력 후 계속 진행

---

## ✅ 실행 방법 (Flink job)

```bash
python consumer/flink_job.py
```

## 이 스크립트는 Flink Python 환경에서 실행되며, 실행 전 다음 환경이 구성되어 있어야 합니다:

- Kafka 실행 중

- PostgreSQL DB 연결 가능

- Elasticsearch 실행 중 (localhost:9200)

- HDFS Web UI 및 파일 시스템 동작 (localhost:9870)

---

## 📈 발전 방향

- ✅ 성능 향상: 병렬 처리 및 배치 크기 조절

- ✅ 정합성 강화: PG/ES 성공 여부에 따라 Kafka ack 연동

- ✅ 전처리 다양화: 뉴스 요약 추가, 개체명 인식 등 NLP 확장

- ✅ 모니터링: 처리 건수, 에러율, 처리 시간 등 지표 수집 및 시각화 (Prometheus + Grafana)

- ✅ 이중 전송 방지: URL 기반 Redis 캐시 추가로 필터링 속도 향상


</details>


<details>
<summary>Batch</summary>

# 🗓️ Batch - Airflow DAG 기반 뉴스 리포트 생성

`batch` 디렉토리는 Apache Airflow DAG를 통해 매일 자동으로 실행되는 뉴스 리포트 작업을 정의합니다. Spark를 통해 집계/분석 작업을 수행하며, HDFS에 저장된 뉴스를 기반으로 리포트를 생성합니다.

또한, Elasticsearch와 PostgreSQL 간 데이터 정합성을 평가하는 스크립트를 포함하여, 전송/저장된 데이터의 신뢰성을 점검할 수 있도록 설계되어 있습니다.

---

## ✅ 주요 역할

- 매일 정해진 시간에 실행되는 **Airflow DAG 등록**
- Spark job을 통해 HDFS에 저장된 뉴스 데이터를 분석
- 뉴스 카테고리, 키워드, 작성일 기준 통계 생성
- 생성된 리포트를 다시 HDFS 또는 PostgreSQL에 저장 가능
- **Elasticsearch vs PostgreSQL 정합성 검증 스크립트 제공**

---

## ⚙️ 구성 요소

- `spark_daily_report.py`: 주요 DAG 스크립트로, 매일 Spark job을 실행
- `spark_job/daily_report.py`: Spark로 리포트를 생성하는 PySpark 스크립트
- `scripts/`: HDFS 경로 생성, 파일 이동, 날짜별 관리 유틸 스크립트 포함
- `scripts/data_integrity_check.py`: Elasticsearch와 PostgreSQL 간 기사 개수 및 키 필드 비교를 통해 정합성 평가

---

## 🔁 처리 흐름

1. Airflow 스케줄러가 매일 DAG를 트리거함
2. Spark job이 로컬에서 뉴스 데이터를 불러옴
3. 카테고리/키워드/날짜별 기사 수, 평균 길이 등 통계 생성
4. 결과는 PDF 형식으로 저장
---

1. 정합성 체크 스크립트를 통해 PostgreSQL ↔ Elasticsearch 비교 수행


---

## ✅ 실행 방식

Airflow docker 실행:

```bash
docker compose up -d
```
localhost:8080 로 접속 후 spark 연결 후 DAG실행

---

## 🛠 요구 환경

- Apache Airflow 2.10.5
- Apache Spark 3.5.4
- Elasticsearch 및 PostgreSQL 서버 실행 중
- Docker 기반 실행

---

## 📈 발전 방향

- ✅ 뉴스 키워드, 카테고리별 트렌드 분석 리포트 생성
- ✅ Slack으로 리포트 자동 전송
- ✅ DAG 성공/실패 여부에 대한 모니터링 및 알림 연동
- ✅ Airflow + Spark + Grafana 연동으로 리포트 시각화 자동화
- ✅ 정합성 체크 결과를 리포트 형태로 로그 및 DB에 저장
- ✅ 다양한 소스의 뉴스 데이터 수집으로 폭 넓은 분석 제공
> ⏱️ 정기적인 배치 처리를 통해 뉴스 추천 품질을 높이고, 사용자 행동 기반 리포트까지 확장 가능합니다.



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


<details>

<summary>Front</summary>
# SSAFYNEWS
- **AI 맞춤 뉴스 추천**  
  카테고리별, 최신순/추천순 필터 제공  

- **뉴스 상세 페이지**  
  기사 '좋아요' 저장, 관련 뉴스 사이드바 제공  

- **대시보드**  
  사용자 활동 시각화: 관심 카테고리, 주요 키워드, 주간 기사 수, 좋아요한 뉴스 등  

---

## 실행 가이드

```bash
npm install

npm run dev
```

---

## 프로젝트 구조

```
FRONTEND/
├── public/
├── src/
│   ├── assets/
│   ├── components/
│   ├── views/
│   ├── router/
│   └── store/
├── package.json
└── vite.config.js
```

---

### Front-end
- main page `/news`
  - NewsView.vue
    기사 리스트를 보여주는 component

    - 카테고리 별   
    ![메인페이지_카테고리별](./public/main_page_keyword.png)   

    - 추천순   
    ![메인페이지_추천순](./public/main_page_recommended.png)   

    - 최신순   
    ![메인페이지_최신순](./public/main_page_lastest.png)
    사용자가 원하는 방식으로 기사 리스트 조회 가능

- detail news page `/news/<int: news_id>`   
  ![뉴스 자세히 보기](./public/Detail_news_page.png)   

  - 뉴스에 대한 자세한 정보 보여주는 component `NewsDetailView.vue`
  - 관련 기사 리스트 제공 `ArticlePreview.vue`
  - 댓글 기능 추가 `CommentBox.vue`   
  ![댓글](./public/comment2.png)   

  - 해당 뉴스 기사에 대해 다양한 정보를 제공해주는 챗봇 추가 (모달 형식) `Chatbot.vue`   
  ![챗봇](./public/sobot.png)
   
- dashboard `/dashboard`   
  ![대시보드](./public/Dashboard.png)
  - 나의 관심 카테고리
  - 내가 본 기사들의 키워드 통계
  - 주간 읽은 기사의 수
  - 좋아요를 누른 기사
  확인 가능
</details>