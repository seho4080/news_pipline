#!/bin/bash
# PostgreSQL 초기화 스크립트
# pgvector extension 설치 및 기본 데이터 설정

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- pgvector extension 생성
    CREATE EXTENSION IF NOT EXISTS vector;
    
    -- 인덱스 최적화를 위한 설정
    ALTER SYSTEM SET shared_preload_libraries = 'vector';
    
    -- 기본 사용자 권한 설정
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
    
    -- 벡터 검색을 위한 인덱스 설정 (Django 마이그레이션 후에 수동으로 실행 필요)
    -- CREATE INDEX CONCURRENTLY ON mynews_news USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
    
    -- 성능 최적화 설정
    ALTER SYSTEM SET work_mem = '256MB';
    ALTER SYSTEM SET maintenance_work_mem = '1GB';
    ALTER SYSTEM SET effective_cache_size = '2GB';
    
    -- 설정 리로드
    SELECT pg_reload_conf();
EOSQL