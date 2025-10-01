# 🔍 Search Engine Configuration

이 폴더는 검색 엔진 관련 설정과 초기화 스크립트를 포함합니다.

## 📁 파일 설명

### Elasticsearch 설정
- **elasticsearch_setup.py**: Elasticsearch 인덱스 생성 및 설정
- **index_mapping.json**: 뉴스 인덱스 매핑 정의
- **analyzer_config.json**: 한국어 텍스트 분석기 설정

### 검색 유틸리티
- **search_utils.py**: 검색 헬퍼 함수 모음
- **query_builder.py**: 동적 쿼리 생성기

---

## 🚀 사용 방법

### 1. Elasticsearch 인덱스 생성
```bash
cd search
python elasticsearch_setup.py
```

### 2. 인덱스 확인
```bash
curl -X GET "localhost:9200/news/_mapping?pretty"
```

### 3. 검색 테스트
```bash
curl -X GET "localhost:9200/news/_search?pretty"
```

---

## 📋 인덱스 구조

### 뉴스 인덱스 매핑
```json
{
  "mappings": {
    "properties": {
      "title": {"type": "text"},
      "content": {"type": "text"}, 
      "writer": {"type": "text"},
      "category": {"type": "keyword"},
      "url": {"type": "text"},
      "keywords": {"type": "keyword"},
      "write_date": {"type": "date"},
      "updated_at": {"type": "date"}
    }
  }
}
```

---

## 🔧 검색 기능

- **전문 검색**: 제목, 내용, 작성자에서 키워드 검색
- **카테고리 필터**: 뉴스 카테고리별 필터링
- **날짜 범위**: 기간별 뉴스 검색
- **키워드 필터**: 특정 키워드로 필터링