# 🐛 로직 오류 및 기능적 문제점 분석 보고서

> **작성일**: 2025-10-31  
> **분석 대상**: News Pipeline 전체 코드베이스

---

## 🔴 심각한 오류 (즉시 수정 필요)

### 1. **ForeignKey 참조 오류** - `models.py` ⚠️⚠️⚠️

#### 문제 코드
```python
# backend/mynews/models.py
class Likes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article_id = models.ForeignKey(news_article, to_field='url', db_column='article_id', on_delete=models.CASCADE)
    #                                              ^^^^^^^^^^^^^^^^
    # ❌ url(TextField)을 ForeignKey로 참조하고 있음!
```

#### 문제점
1. **Primary Key가 아닌 필드를 FK로 사용**: `url`은 `unique=True`지만 성능 문제 발생
2. **필드명 혼동**: `article_id`라는 이름이지만 실제로는 URL 문자열 저장
3. **Join 성능 저하**: 긴 텍스트(URL)로 조인하면 인덱스 효율 급감
4. **Serializer와 불일치**:
   ```python
   # serializers.py
   def get_total_like(self, obj):
       return Likes.objects.filter(article_id=obj).count()
       #                           ^^^^^^^^^^^^^^^^
       # obj는 news_article 인스턴스인데 article_id는 URL을 기대함!
   ```

#### 영향
- **Likes.objects.filter(article_id=obj)** → `obj.url`을 전달해야 하는데 객체를 전달하면 쿼리 실패
- 실제로는 작동하지 않을 가능성 높음

#### 해결책
```python
# 올바른 방법 1: Primary Key 사용
class Likes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(news_article, on_delete=models.CASCADE)  # ✅ PK 자동 사용
    
    class Meta:
        unique_together = ('user', 'article')
        db_table = 'likes'

# Serializer도 수정
def get_total_like(self, obj):
    return Likes.objects.filter(article=obj).count()  # ✅ 수정됨
```

---

### 2. **Reads 모델도 동일한 문제** ⚠️⚠️⚠️

#### 문제 코드
```python
class Reads(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article_id = models.ForeignKey(news_article, to_field='url', db_column='article_id', on_delete=models.CASCADE)
    #                                              ^^^^^^^^^^^^^^^^
    # ❌ 동일한 문제!
```

#### 해결책
```python
class Reads(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(news_article, on_delete=models.CASCADE)  # ✅ 수정
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'read'
        indexes = [
            models.Index(fields=['user', 'article', '-read_at']),
        ]
```

---

### 3. **Consumer의 DLQ Producer 조건문 오류** ⚠️⚠️

#### 문제 코드
```python
# consumer/news_preprocessor.py

except Exception as e:
    log.exception("JSON 디코드 실패")
    if producer:
            if producer is not None and DLQ_TOPIC:  # ❌ 중복 체크
                producer.produce(DLQ_TOPIC, msg.value())
    consumer.commit(msg)
```

#### 문제점
1. **중복 체크**: `if producer:` 다음에 또 `if producer is not None` 체크
2. **DLQ_TOPIC 문자열 체크**: 빈 문자열("")도 환경 변수로 설정 가능한데 `if DLQ_TOPIC`은 빈 문자열을 `False`로 판단
3. **여러 곳에서 반복**: 같은 패턴이 3군데 이상 반복됨

#### 해결책
```python
# 파일 상단에 헬퍼 함수 추가
def send_to_dlq(producer, topic, data, reason="unknown"):
    """DLQ에 메시지 전송 (헬퍼 함수)"""
    if not producer or not topic:
        return
    
    payload = {
        "reason": reason,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "data": data
    }
    producer.produce(topic, json.dumps(payload, ensure_ascii=False).encode("utf-8"))

# 사용 예시
except Exception as e:
    log.exception("JSON 디코드 실패")
    send_to_dlq(producer, DLQ_TOPIC, msg.value().decode("utf-8"), "json_decode_error")
    consumer.commit(msg)
```

---

### 4. **Producer의 URL 인코딩 버그** ⚠️⚠️

#### 문제 코드
```python
# producer/produce.py

# Kafka로 전송
key = quote(article['url'])  # URL을 키로 사용 (중복 방지)
future = producer.send(KAFKA_TOPIC, key=key, value=article)
```

#### 문제점
1. **Consumer에서 디코딩 안함**: Consumer에서 `msg.key()`를 사용할 때 URL 디코딩 필요
2. **Elasticsearch에서도 인코딩**:
   ```python
   # consumer/news_preprocessor.py
   doc_id = quote(url, safe="")  # ✅ 여기서도 인코딩
   ```
   → 두 번 인코딩되거나 불일치 가능성

#### 해결책
```python
# producer/produce.py - 인코딩하지 않고 원본 사용
key = article['url']  # ✅ 원본 URL 사용
future = producer.send(KAFKA_TOPIC, key=key, value=article)

# consumer에서도 원본 사용
doc_id = quote(url, safe="")  # ES ID는 인코딩 필요 (특수문자 때문)
```

---

## 🟡 중요한 문제 (1주일 내 수정)

### 5. **pgvector 어댑터 누락** ⚠️⚠️

#### 문제 코드
```python
# consumer/news_preprocessor.py

if USE_PGVECTOR:
    cur.execute("""
        INSERT INTO news_article (...)
        VALUES (%s,%s,%s,%s,%s,%s,%s, %s::vector)
    """, (
        # ...
        f"[{', '.join(str(x) for x in row['embedding'])}]"  # ❌ 문자열로 변환
    ))
```

#### 문제점
1. **psycopg2는 pgvector를 기본 지원하지 않음**: `pgvector` 라이브러리 필요
2. **문자열로 변환하면 타입 오류 발생 가능**
3. **Django ORM과 불일치**:
   ```python
   # models.py
   embedding = VectorField(dimensions=1536)  # ✅ Django는 pgvector-django 사용
   ```

#### 해결책
```python
# consumer/news_preprocessor.py

from pgvector.psycopg2 import register_vector

def insert_article(pool, row):
    conn = pool.getconn()
    register_vector(conn)  # ✅ pgvector 어댑터 등록
    
    try:
        with conn.cursor() as cur:
            if USE_PGVECTOR:
                cur.execute("""
                    INSERT INTO news_article (...)
                    VALUES (%s,%s,%s,%s,%s,%s,%s, %s)
                """, (
                    # ...
                    row["embedding"]  # ✅ 리스트 그대로 전달
                ))
            # ...
```

---

### 6. **Elasticsearch 검색 결과와 DB 순서 불일치** ⚠️⚠️

#### 문제 코드
```python
# backend/mynews/views.py

urls = [hit["_source"]["url"] for hit in es_result["hits"]["hits"]]

# PostgreSQL 조회
query_sql = f"""
    SELECT title, writer, write_date, category, url
    FROM news_article
    WHERE url IN ({placeholder})
"""
# ❌ ES의 순서(relevance score)가 사라짐!
```

#### 문제점
1. **검색 순위 무시**: Elasticsearch는 relevance score 순으로 정렬하지만 SQL `IN`은 순서 보장 안함
2. **사용자 혼란**: 검색 결과가 관련도 순이 아니라 랜덤처럼 보임

#### 해결책
```python
# 방법 1: SQL ORDER BY CASE
url_to_rank = {url: idx for idx, url in enumerate(urls)}
placeholder = ','.join(['%s'] * len(urls))

query_sql = f"""
    SELECT title, writer, write_date, category, url
    FROM news_article
    WHERE url IN ({placeholder})
    ORDER BY CASE url
        {' '.join(f"WHEN %s THEN {i}" for i, _ in enumerate(urls))}
    END
"""
cursor.execute(query_sql, urls + urls)  # 두 번 전달

# 방법 2: Python에서 정렬 (더 간단)
with connection.cursor() as cursor:
    cursor.execute(query_sql, urls)
    rows = cursor.fetchall()

# 딕셔너리로 변환 후 ES 순서대로 정렬
url_to_row = {row[4]: row for row in rows}  # row[4]가 url
sorted_rows = [url_to_row[url] for url in urls if url in url_to_row]

results = [
    {
        "title": row[0],
        "writer": row[1],
        "write_date": row[2],
        "category": row[3],
        "url": row[4],
    }
    for row in sorted_rows  # ✅ ES 순서 유지
]
```

---

### 7. **세션 직렬화 오류 (Chatbot)** ⚠️⚠️

#### 문제 코드
```python
# backend/mynews/views.py

if session_key not in request.session:
    prompt = f"""너는 친절한 뉴스 비서 <소봇>이야. ..."""
    request.session[session_key] = [SystemMessage(content=prompt)]
    # ❌ LangChain 객체를 세션에 직접 저장!
```

#### 문제점
1. **Django 세션은 JSON 직렬화**: `SystemMessage` 객체는 직렬화 불가
2. **에러 발생**: `TypeError: Object of type 'SystemMessage' is not JSON serializable`
3. **코드 하단에서는 수정됨**:
   ```python
   request.session[session_key] = [message_to_dict(m) for m in messages]  # ✅ 이건 올바름
   ```

#### 해결책
```python
# 초기화 시에도 dict로 저장
if session_key not in request.session:
    prompt = f"""너는 친절한 뉴스 비서 <소봇>이야. ..."""
    request.session[session_key] = [
        {"role": "system", "content": prompt}  # ✅ dict로 저장
    ]

# 사용 시 dict → LangChain 객체로 변환
messages_dict = request.session.get(session_key, [])
messages = [dict_to_message(d) for d in messages_dict]
messages.append(HumanMessage(content=question))
```

---

### 8. **Airflow DAG 파일 이동 로직 누락** ⚠️

#### 문제 코드
```python
# batch/dags/spark_daily_report_dag.py

move_daily = PythonOperator(
    task_id = 'move_daily_data_task',
    python_callable = move_daily_data.move_file,  # ✅ 호출
)
```

#### 문제점
1. **`spark_daily_report.py`에는 이동 로직 없음**:
   ```python
   # TODO: 데이터 처리, 리포트 저장, realtime 파일 -> news_archive로 이동 등
   # realtime에 있는 json파일을 news_archive로 이동 
   # ❌ 실제 코드 없음!
   ```
2. **`move_daily_data.move_file` 함수 미구현**: import하지만 실제 파일 없을 가능성

#### 해결책
```python
# batch/dags/scripts/move_daily_data.py (새 파일 생성)

import os
import shutil
from datetime import datetime

def move_file(**context):
    """realtime 디렉토리의 JSON 파일을 news_archive로 이동"""
    realtime_dir = "/opt/airflow/data/realtime"
    archive_dir = "/opt/airflow/data/news_archive"
    
    # 날짜별 폴더 생성
    date_str = context['ds']  # Airflow의 실행 날짜
    target_dir = os.path.join(archive_dir, date_str)
    os.makedirs(target_dir, exist_ok=True)
    
    # JSON 파일 이동
    moved_count = 0
    for filename in os.listdir(realtime_dir):
        if filename.endswith('.json'):
            src = os.path.join(realtime_dir, filename)
            dst = os.path.join(target_dir, filename)
            shutil.move(src, dst)
            moved_count += 1
    
    print(f"✅ {moved_count}개 파일을 {target_dir}로 이동 완료")
    return moved_count

# DAG에서 사용
from scripts import move_daily_data

move_daily = PythonOperator(
    task_id='move_daily_data_task',
    python_callable=move_daily_data.move_file,
    provide_context=True,  # ✅ context 전달
)
```

---

## 🟢 개선 필요 (경미한 문제)

### 9. **Producer 재시도 시 sleep 없음**

#### 문제 코드
```python
# producer/produce.py

def fetch_rss(rss_url, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            # ...
            return feed
        except Exception as e:
            logger.error(f"RSS 피드 가져오기 실패 (시도 {attempt + 1}/{retries})")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # ✅ 있음
            else:
                logger.error(f"RSS 피드 최종 실패: {rss_url}")
                return None
```

**이건 사실 문제 없음**! 다만 `crawl_article`에서는 다름:

```python
def crawl_article(url, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            # ...
        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(1 * (attempt + 1))  # ✅ 선형 백오프 (1초, 2초, 3초)
```

**일관성 문제**: 한쪽은 지수 백오프, 한쪽은 선형 백오프

#### 해결책
```python
# 통일된 재시도 데코레이터 사용
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def fetch_rss(rss_url):
    # 재시도 로직 제거, tenacity가 자동 처리
    # ...
```

---

### 10. **keywords 필드 타입 불일치**

#### 문제
```python
# models.py
keywords = models.TextField(null=True, blank=True)  # ❌ 문자열
# keywords = models.JSONField(null=True, blank=True)  # ✅ 주석 처리됨

# consumer에서는 JSON 문자열로 저장
json.dumps(row["keywords"], ensure_ascii=False)

# Serializer에서는 파싱
if isinstance(keywords_raw, str):
    try:
        rep['keywords'] = json.loads(keywords_raw)
```

#### 문제점
- **불필요한 직렬화/역직렬화**: JSONField 쓰면 자동 처리
- **에러 가능성**: JSON 파싱 실패 시 빈 배열 반환

#### 해결책
```python
# models.py
keywords = models.JSONField(null=True, blank=True, default=list)  # ✅ JSONField 사용

# consumer에서 그냥 리스트로 저장
cur.execute("""...""", (..., row["keywords"], ...))  # psycopg2가 자동 변환

# Serializer에서 파싱 불필요
class ArticleDetailSerializer(serializers.ModelSerializer):
    # to_representation에서 keywords 처리 제거
```

---

### 11. **map_functions.py 사용 안함**

#### 문제 코드
```python
# consumer/map_functions.py
class NewsEnricher(MapFunction):
    def map(self, msg: str):
        # PyFlink MapFunction
        # ...
```

#### 문제점
- **어디서도 import 안함**: 사용되지 않는 코드
- **PyFlink 의존성**: `requirements.txt`에 pyflink 없음
- **Kafka Consumer와 중복**: `news_preprocessor.py`가 이미 전처리 수행

#### 해결책
1. **사용한다면**: PyFlink 스트리밍 파이프라인 구축
2. **사용 안한다면**: 파일 삭제

---

### 12. **Comment Serializer의 read_only_fields 오류**

#### 문제 코드
```python
# serializers.py

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            'id',
            'user',         # 사용자 ID
            'username',     # 읽기용
            'article',      # 기사 ID
            'content',
            # ...
        ]
        read_only_fields = ['user', 'article']  # ❌ 문제 발생 가능
```

#### 문제점
- **POST 시 article 전달 방법 불명확**:
  ```python
  # views.py
  def post(self, request, article_id):
      serializer = CommentSerializer(data=request.data)
      if serializer.is_valid():
          comment = serializer.save(user=request.user, article_id=article_id)
          #                                              ^^^^^^^^^^^^^^^^^^^
          # article_id는 URL 파라미터인데 save에 전달
  ```

#### 해결책
```python
# views.py
def post(self, request, article_id):
    try:
        article = news_article.objects.get(id=article_id)
    except news_article.DoesNotExist:
        return Response({"error": "기사를 찾을 수 없습니다."}, status=404)
    
    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        comment = serializer.save(user=request.user, article=article)  # ✅ 객체 전달
        return Response(CommentSerializer(comment).data, status=201)
    return Response(serializer.errors, status=400)
```

---

## 📊 로직 정합성 체크

### 13. **유사 기사 추천의 exclude 로직**

#### 코드
```python
# views.py
similar_qs = (
    news_article.objects
    .exclude(id=article_id)  # ✅ 자기 자신 제외
    .annotate(similarity=CosineDistance('embedding', target.embedding))
    .order_by('similarity')[:10]
)
```

**이건 올바름!** 다만:
- `CosineDistance`는 **거리**이므로 값이 작을수록 유사함 (올바름)
- `CosineSimilarity` (Django 없음)는 값이 클수록 유사함

---

### 14. **날짜 파싱 폴백**

#### 코드
```python
# consumer/news_preprocessor.py
def parse_date(s: str) -> datetime.datetime:
    if not s:
        return datetime.datetime(1990,1,1)  # ❌ 1990년?
    try:
        return date_parser.parse(s)
    except Exception:
        return datetime.datetime(1990,1,1)  # ❌ 1990년?
```

#### 문제점
- **1990년이 의미있는 값인가?**: 차라리 현재 시간이 낫지 않나?
- **로깅 없음**: 파싱 실패를 알 수 없음

#### 해결책
```python
def parse_date(s: str) -> datetime.datetime:
    if not s:
        log.warning("날짜 값이 없음, 현재 시간 사용")
        return datetime.datetime.utcnow()
    try:
        return date_parser.parse(s)
    except Exception as e:
        log.warning(f"날짜 파싱 실패: {s}, 현재 시간 사용. Error: {e}")
        return datetime.datetime.utcnow()  # ✅ 더 합리적
```

---

## 🔍 발견된 잠재적 버그

### 15. **Spark DataFrame ID 컬럼**

#### 코드
```python
# batch/dags/scripts/spark_daily_report.py

data = [
    ["총 기사 수", len(df_keywords.select("id").distinct().collect())],
    #                                      ^^^^
    # ❌ JSON에 'id' 필드가 있나?
]
```

#### 문제점
- **Producer가 보내는 데이터**:
  ```python
  article_data = {
      'title': ...,
      'write_date': ...,
      'content': ...,
      'url': ...,
      # 'id' 필드 없음!
  }
  ```
- **Spark가 JSON 읽을 때**: 'id' 컬럼이 없으면 에러

#### 해결책
```python
# url을 고유 식별자로 사용
data = [
    ["총 기사 수", df_keywords.select("url").distinct().count()],  # ✅ count() 사용
    # ...
]
```

---

## ✅ 정리 및 우선순위

### 🔴 즉시 수정 (시스템 작동 안함)
1. ✅ **Likes/Reads 모델 ForeignKey 수정** - to_field='url' 제거
2. ✅ **Serializer 필터 수정** - `article_id=obj` → `article=obj`
3. ✅ **pgvector 어댑터 등록**
4. ✅ **Spark 'id' 컬럼 → 'url' 변경**

### 🟡 1주일 내 수정 (기능 개선)
5. ✅ **Elasticsearch 검색 순서 유지**
6. ✅ **Chatbot 세션 초기화 수정**
7. ✅ **파일 이동 로직 구현** (Airflow DAG)
8. ✅ **DLQ 조건문 단순화**

### 🟢 여유 있을 때 개선
9. ✅ **keywords를 JSONField로 변경**
10. ✅ **재시도 로직 통일** (tenacity 사용)
11. ✅ **날짜 파싱 폴백 개선**
12. ✅ **사용 안하는 map_functions.py 제거**

---

## 🧪 테스트 시나리오

### 테스트 1: Likes 기능
```python
# Django shell
from mynews.models import news_article, Likes
from members.models import User

user = User.objects.first()
article = news_article.objects.first()

# 좋아요 생성
like = Likes.objects.create(user=user, article=article)  # ✅ 작동해야 함

# 좋아요 개수
count = Likes.objects.filter(article=article).count()
print(f"좋아요 수: {count}")  # ✅ 1이어야 함
```

### 테스트 2: Serializer
```python
from mynews.serializers import ArticleDetailSerializer
from django.test import RequestFactory

factory = RequestFactory()
request = factory.get('/')
request.user = user

serializer = ArticleDetailSerializer(article, context={'request': request})
print(serializer.data['total_like'])  # ✅ 1이어야 함
print(serializer.data['is_like'])     # ✅ True여야 함
```

### 테스트 3: Consumer + DB
```bash
# Kafka에 테스트 메시지 전송
echo '{
  "title": "테스트 기사",
  "url": "http://test.com/1",
  "content": "홍길동 기자 테스트 내용입니다.",
  "write_date": "2025-10-31T10:00:00+09:00"
}' | kafka-console-producer.sh --topic news-raw --bootstrap-server localhost:9092

# PostgreSQL에서 확인
psql -U newsuser -d newsdb -c "SELECT title, writer, category FROM news_article WHERE url='http://test.com/1';"
```

---

## 📝 수정 체크리스트

```markdown
### 긴급 (오늘)
- [ ] Likes 모델 ForeignKey 수정
- [ ] Reads 모델 ForeignKey 수정
- [ ] ArticleDetailSerializer.get_total_like() 수정
- [ ] ArticleDetailSerializer.get_total_read() 수정
- [ ] ArticleDetailSerializer.get_is_like() 수정
- [ ] ArticleListSerializer도 동일하게 수정
- [ ] Migration 생성 및 적용
- [ ] 테스트 실행

### 이번 주
- [ ] pgvector 어댑터 등록 (consumer/news_preprocessor.py)
- [ ] Elasticsearch 검색 순서 유지
- [ ] Chatbot 세션 초기화 수정
- [ ] move_daily_data.py 구현
- [ ] Spark DataFrame 'id' → 'url' 수정
- [ ] DLQ 조건문 헬퍼 함수로 리팩토링

### 여유 있을 때
- [ ] keywords 필드를 JSONField로 변경
- [ ] tenacity로 재시도 로직 통일
- [ ] 날짜 파싱 폴백 개선
- [ ] map_functions.py 사용 여부 결정
```

---

**총평**: 전체적인 아키텍처는 훌륭하지만, **모델 관계 설정의 근본적인 오류**로 인해 Likes/Reads 기능이 제대로 작동하지 않을 가능성이 높습니다. 이 부분을 최우선으로 수정해야 합니다.
