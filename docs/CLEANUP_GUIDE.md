# 🧹 프로젝트 정리 가이드

## 📋 정리된 폴더 구조

프로젝트 구조가 다음과 같이 정리되었습니다:

### ✅ 주요 서비스 폴더
- **frontend/** - React 18 프론트엔드 (메인)
- **backend/** - Django 백엔드
- **producer/** - Kafka Producer (RSS 크롤러)
- **consumer/** - Kafka Consumer (AI 전처리)
- **batch/** - Airflow + Spark 배치 처리

### ✅ 설정 및 인프라 폴더
- **docker/** - Docker 컨테이너 설정
- **config/** - 설정 파일 모음
- **search/** - Elasticsearch 검색 설정
- **scripts/** - 유틸리티 및 테스트 스크립트
- **docs/** - 문서 모음
- **api_docs/** - API 문서 및 ERD

---

## 🗂️ 파일 이동 내역

### 이동된 파일들
```
elastic_search.py → search/elasticsearch_setup.py
flink.py → consumer/flink_processor.py
news_processor.py → scripts/news_processor_standalone.py
extract_pgvector.py → scripts/extract_pgvector_test.py
load_pgvector.py → scripts/load_pgvector_test.py
insert_data_into_psql.py → scripts/insert_csv_to_psql.py
docker-compose-elastic.yml → config/docker-compose-elastic.yml
```

### ✅ 정리 완료된 항목
```bash
# 이동 완료된 파일들
elastic_search.py → search/elasticsearch_setup.py
flink.py → consumer/flink_processor.py  
news_processor.py → scripts/news_processor_standalone.py
extract_pgvector.py → scripts/extract_pgvector_test.py
load_pgvector.py → scripts/load_pgvector_test.py
insert_data_into_psql.py → scripts/insert_csv_to_psql.py
docker-compose-elastic.yml → config/docker-compose-elastic.yml

# 삭제 완료된 중복 파일들
✅ elastic_search.py (루트)
✅ flink.py (루트)  
✅ news_processor.py (루트)
✅ extract_pgvector.py (루트)
✅ load_pgvector.py (루트)
✅ insert_data_into_psql.py (루트)
✅ docker-compose-elastic.yml (루트)
```

### 🔄 남은 정리 항목
- **frontend-vue-backup/** - Vue.js 백업 (필요시 삭제)
- **frontend-react/** - React 메인 프론트엔드 (권한 문제로 이동 보류)

---

## 🔧 정리 후 실행 방법

### 1. 검색 엔진 설정
```bash
cd search
python elasticsearch_setup.py
```

### 2. 테스트 스크립트 실행
```bash
cd scripts
python extract_pgvector_test.py
python news_processor_standalone.py
```

### 3. Docker 서비스 실행
```bash
# 전체 스택 실행
./docker/scripts/setup.sh
./docker/scripts/build.sh  
./docker/scripts/deploy.sh start

# Elasticsearch만 실행
cd config
docker-compose -f docker-compose-elastic.yml up -d
```

---

## 📝 추가 정리 권장 사항

### ✅ 삭제 완료된 파일/폴더
```bash
# 중복 파일들 (이미 삭제 완료)
✅ elastic_search.py
✅ flink.py  
✅ news_processor.py
✅ extract_pgvector.py
✅ load_pgvector.py
✅ insert_data_into_psql.py
✅ docker-compose-elastic.yml
```

### 🔄 수동 정리 필요한 항목
```bash
# 프론트엔드 정리 (권한 문제로 수동 처리 필요)
# Windows에서는 파일 탐색기를 통해 수행 권장:
# 1. frontend-react/ 폴더를 frontend/로 이름 변경
# 2. frontend-vue-backup/ 폴더는 백업 보관 후 삭제

# 또는 관리자 권한으로 실행:
# mv frontend-react frontend
# rm -rf frontend-vue-backup  # Vue 백업이 불필요한 경우
```

### 백업 권장 파일
- `.env` (개인 설정)
- `data/` 폴더 (있는 경우)
- 개인 수정 사항이 있는 설정 파일들

---

## 🎯 정리 완료 후 이점

1. **구조화된 프로젝트**: 역할별 폴더 분리로 유지보수성 향상
2. **명확한 문서**: 각 폴더별 README.md로 사용법 안내
3. **효율적인 개발**: 관련 파일들의 논리적 그룹핑
4. **쉬운 배포**: Docker 기반 원클릭 배포
5. **확장성**: 새 기능 추가 시 적절한 폴더에 배치 가능

---

## 🔄 지속적인 정리 방법

- **새 파일 생성 시**: 적절한 폴더에 배치
- **기능 추가 시**: 관련 폴더에 그룹핑
- **설정 변경 시**: config/ 폴더 활용
- **문서 업데이트**: 변경 사항 시 해당 README.md 수정