# Producer Dockerfile for Kafka Producer
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 설치
COPY docker/requirements/producer-requirements.txt .
RUN pip install --no-cache-dir -r producer-requirements.txt

# Producer 코드 복사
COPY producer/ .

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "from kafka import KafkaProducer; KafkaProducer(bootstrap_servers='kafka:9092')" || exit 1

# Producer 실행
CMD ["python", "produce.py"]