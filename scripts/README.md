# 🔧 Utility Scripts

이 폴더는 프로젝트 운영 및 관리를 위한 유틸리티 스크립트들을 포함합니다.

## 📁 스크립트 분류

### 🧪 테스트 스크립트
- **extract_pgvector_test.py**: RSS 수집 및 pgvector 테스트
- **load_pgvector_test.py**: PostgreSQL 연결 및 데이터 적재 테스트
- **insert_csv_to_psql.py**: CSV 데이터를 PostgreSQL로 일괄 삽입

### ⚙️ 처리 스크립트
- **news_processor_standalone.py**: 독립 실행형 뉴스 처리기
- **data_migration.py**: 데이터 마이그레이션 유틸리티
- **backup_restore.py**: 데이터 백업 및 복원

### 🔍 모니터링 스크립트
- **health_check.py**: 서비스 상태 점검
- **performance_monitor.py**: 성능 모니터링 도구
- **log_analyzer.py**: 로그 분석 유틸리티

---

## 🚀 사용 방법

### 테스트 실행
```bash
cd scripts

# RSS 수집 테스트
python extract_pgvector_test.py

# 데이터베이스 연결 테스트
python load_pgvector_test.py

# CSV 데이터 삽입
python insert_csv_to_psql.py
```

### 데이터 처리
```bash
# 독립 실행형 뉴스 처리
python news_processor_standalone.py

# 데이터 마이그레이션
python data_migration.py --source=old_db --target=new_db
```

### 모니터링
```bash
# 서비스 상태 점검
python health_check.py

# 성능 모니터링
python performance_monitor.py --duration=60
```

---

## ⚠️ 주의사항

- **환경 설정**: 실행 전 .env 파일 설정 확인
- **의존성**: requirements.txt의 패키지 설치 필요
- **권한**: 데이터베이스 접근 권한 확인
- **백업**: 중요한 작업 전 반드시 데이터 백업

---

## 🔧 스크립트 개발

새로운 스크립트 작성 시:
1. 적절한 로깅 설정
2. 에러 핸들링 포함
3. 실행 옵션 (argparse) 활용
4. 도움말 및 사용 예시 제공