# Consumer Dockerfile for news_preprocessor.py
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 설치
COPY docker/requirements/consumer-requirements.txt .
RUN pip install --no-cache-dir -r consumer-requirements.txt

# Consumer 코드 복사
COPY consumer/ .
COPY news_preprocessor.py .

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "from confluent_kafka import Consumer; Consumer({'bootstrap.servers': 'kafka:9092', 'group.id': 'health-check'})" || exit 1

# Consumer 실행
CMD ["python", "news_preprocessor.py"]