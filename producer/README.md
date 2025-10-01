# 📰 Producer

연합뉴스 RSS 피드에서 뉴스 데이터를 수집하고, 본문 내용을 크롤링하여 Kafka로 전송하는 enterprise-grade 뉴스 프로듀서입니다.

---

## ✅ 주요 기능

- 연합뉴스의 다양한 카테고리(RSS 피드)에서 뉴스 수집
- 뉴스 기사 본문을 크롤링하여 콘텐츠 보강
- Kafka 토픽으로 실시간 데이터 전송 (`news-topic`)
- 기사 제목, 작성일, 본문, URL 정보를 JSON 형태로 전송
- **🆕 Production-ready 기능들:**
  - 지수 백오프를 통한 retry 로직
  - 포괄적인 에러 핸들링 및 로깅
  - 환경 변수 기반 설정 관리
  - Kafka 최적화 (압축, acks='all')
  - 성공/실패 모니터링 및 통계

---

## 📦 사용 라이브러리

- `feedparser`: RSS 파싱
- `beautifulsoup4`: HTML 본문 크롤링
- `requests`: 웹 요청 처리
- `kafka-python`: Kafka 메시지 전송
- `python-dotenv`: 환경 변수 관리
- `logging`: 구조화된 로깅

---

## 🛠️ 설정값 및 환경변수

환경 변수를 통해 설정을 관리합니다. `.env.example`을 참고하여 `.env` 파일을 생성하세요.

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=news-topic

# RSS Configuration  
RSS_TIMEOUT=30
RSS_MAX_RETRIES=3

# Crawling Configuration
CRAWL_TIMEOUT=15
CRAWL_MAX_RETRIES=3
CRAWL_DELAY=1

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=producer.log
```

---

## 🧪 설치 및 실행 방법

### 1. 의존성 설치
```bash
cd producer
pip install -r requirements.txt
```

### 2. 환경 설정
```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# 필요에 따라 .env 파일의 설정값 조정
```

### 3. Kafka 실행
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

### 4. Producer 실행
```bash
# Kafka 서버가 실행 중이어야 함
python produce.py
```

---

## 📊 모니터링 및 로깅

Producer는 다음과 같은 모니터링 기능을 제공합니다:

- **구조화된 로깅**: 콘솔 + 파일 로깅 (producer.log)
- **성공/실패 통계**: RSS 수집 및 Kafka 전송 현황
- **에러 상세 로그**: 실패 원인 및 재시도 정보
- **진행률 표시**: 실시간 처리 상황 모니터링

### 로그 예시
```
2024-01-15 10:30:15 - INFO - RSS 수집 시작: https://rss.yonhapnews.co.kr/politics.xml
2024-01-15 10:30:16 - INFO - 25개 뉴스 기사 발견
2024-01-15 10:30:18 - INFO - Kafka 전송 성공: 정부, 새해 경제정책 발표
2024-01-15 10:30:19 - WARNING - 크롤링 재시도 (1/3): connection timeout
2024-01-15 10:30:21 - INFO - 수집 완료 - 성공: 24/25, 실패: 1/25
```

---

## 🔧 기술 특징

### 1. 안정성 (Reliability)
- **지수 백오프 retry**: 네트워크 오류 시 점진적 재시도
- **타임아웃 처리**: RSS 수집/크롤링 각각 독립적 타임아웃
- **Graceful degradation**: 일부 기사 실패해도 전체 프로세스 지속

### 2. 성능 최적화 (Performance)
- **Kafka 압축**: gzip 압축으로 네트워크 효율성 증대
- **배치 처리**: 여러 메시지를 효율적으로 배치 전송
- **연결 재사용**: Kafka producer 연결 풀링

### 3. 운영 편의성 (Operations)
- **환경 변수 설정**: 코드 수정 없이 설정 변경 가능
- **상세 로깅**: 문제 진단을 위한 충분한 로그 정보
- **통계 리포팅**: 수집 성공률 및 실패 원인 분석

---

## ⚠️ 주의사항

1. **율제한 (Rate Limiting)**: 각 RSS 피드 간 1초 간격 유지
2. **메모리 사용량**: 대량 뉴스 처리 시 메모리 모니터링 필요
3. **네트워크 안정성**: 안정적인 인터넷 연결 환경에서 실행 권장
4. **Kafka 용량**: 뉴스 데이터 축적에 따른 디스크 공간 관리 필요

---

## 🚀 개선사항 (2024년 업데이트)

### ✅ **완료된 개선사항**
- ✅ **에러 핸들링 및 재전송 로직** 구현 (retry, exponential backoff)
- ✅ 전송 성공/실패 **로깅 및 메트릭 수집**
- ✅ **환경 변수 기반 설정 관리**
- ✅ **구조화된 로깅 시스템** (파일 + 콘솔)
- ✅ **Kafka 최적화** (압축, acks='all', 배치 설정)
- ✅ **타임아웃 및 재시도 로직** 세분화

### 🔄 **진행 중인 개선사항**
- 🔄 **스케줄링 자동화** (Airflow DAG 연동)
- 🔄 **모니터링 대시보드** 구축
- 🔄 **성능 메트릭** 수집 및 분석

### 📋 **향후 계획**
- 📋 **수집 대상 확장**: 다양한 언론사 RSS 피드 추가
- 📋 **Kafka 토픽 분리**: 카테고리별 토픽 분리로 처리 유연성 증가
- 📋 **데이터 유효성 검사**: 불완전한 뉴스 필터링 강화
- 📋 **다국어 지원**: 해외 뉴스 수집 기능 추가