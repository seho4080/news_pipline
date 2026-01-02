# 📑 뉴스 파이프라인 프로젝트 완벽 가이드

**프로덕션 레벨 뉴스 데이터 처리 시스템**의 완벽한 설명서입니다.

---

## 📖 문서 네비게이션

### 🚀 빠른 시작
- [QUICKSTART.md](consumer/QUICKSTART.md) - 5분 안에 실행하기
- [README.md](consumer/README.md) - 프로젝트 개요

### 📊 아키텍처 & 설계
- [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md) - 전체 시스템 아키텍처
- [DOCKER_OPTIMIZATION.md](DOCKER_OPTIMIZATION.md) - Docker Compose 최적화

### � 품질 & 규정
- [SQA_ISO9001_ASSESSMENT.md](SQA_ISO9001_ASSESSMENT.md) - SQA 관점 품질 평가 및 ISO 9001 준수 현황
- [COMPLETION_REPORT.md](COMPLETION_REPORT.md) - 프로젝트 완성 보고서

### �💻 Consumer 가이드
- [DLQ_GUIDE.md](consumer/DLQ_GUIDE.md) - 실패 메시지 처리
- [DEPLOYMENT_CHECKLIST.md](consumer/DEPLOYMENT_CHECKLIST.md) - 배포 전 체크리스트
- [consumer/requirements.txt](consumer/requirements.txt) - 파이썬 의존성

### 🏢 프로덕션 운영
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - 배포 상세 가이드
- [OPERATIONS_MANUAL.md](OPERATIONS_MANUAL.md) - 일일 운영 매뉴얼
- [PROJECT_README.md](PROJECT_README.md) - 프로젝트 통합 문서

### ⚙️ 설정 & 환경
- [.env.example](consumer/.env.example) - 환경 변수 템플릿
- [docker-compose.yml](docker-compose.yml) - 개발 환경 구성
- [docker-compose.prod.yml](docker-compose.prod.yml) - 프로덕션 환경 구성

---

## 🗺️ 읽기 순서 (목적별)

### 1️⃣ 첫 시작하는 개발자
```
1. QUICKSTART.md (README 포함)
2. PIPELINE_ARCHITECTURE.md
3. consumer/README.md
4. consumer 코드 직접 살펴보기
```

### 2️⃣ 배포 담당자
```
1. DEPLOYMENT_CHECKLIST.md
2. DOCKER_OPTIMIZATION.md
3. PRODUCTION_DEPLOYMENT.md
4. OPERATIONS_MANUAL.md
```

### 3️⃣ 운영 엔지니어
```
1. OPERATIONS_MANUAL.md
2. DLQ_GUIDE.md
3. DOCKER_OPTIMIZATION.md
4. 모니터링 설정 (OPERATIONS_MANUAL 참고)
```

### 4️⃣ 시스템 아키텍처 담당자
```
1. PIPELINE_ARCHITECTURE.md
2. PROJECT_README.md
3. DOCKER_OPTIMIZATION.md
4. PRODUCTION_DEPLOYMENT.md
```

---

## 📚 문서 상세 설명

### 1. QUICKSTART.md (⭐ 필수)
**대상:** 모든 개발자  
**내용:**
- 환경 설정 (Python, Docker)
- 로컬 실행 (docker-compose up -d)
- 초기 데이터 로드
- 기본 명령어
- 일반적인 문제 해결

**예상 시간:** 20분

---

### 2. PIPELINE_ARCHITECTURE.md (⭐ 필수)
**대상:** 시스템 이해가 필요한 모든 사람  
**내용:**
```
┌─────────────┐
│ Producer    │ → Kafka Topic (news-topic)
└─────────────┘
                ↓
        ┌──────────────┐
        │ Consumer     │
        │ (Kafka)      │
        └──────────────┘
                ↓
    ┌──────────────┬──────────────┐
    ↓              ↓
┌─────────┐  ┌──────────────┐
│ PostgreSQL   │  Elasticsearch │
└─────────┘  └──────────────┘
    ↑              ↑
    └──────────────┘
         (API)
```

- 메시지 흐름
- 데이터 저장소 구조
- 실패 처리 (DLQ)
- 성능 특성

**예상 시간:** 30분

---

### 3. consumer/README.md
**대상:** Consumer 개발/유지보수 담당자  
**내용:**
- Consumer 상세 기능
- 코드 구조
- 환경 변수 설명
- 로깅 및 모니터링

**예상 시간:** 20분

---

### 4. consumer/QUICKSTART.md
**대상:** Consumer만 개발하는 경우  
**내용:**
- Consumer 단독 실행 방법
- 의존성 설치
- 테스트 실행
- 디버깅 팁

**예상 시간:** 15분

---

### 5. consumer/DLQ_GUIDE.md
**대상:** 운영 담당자, 문제 해결 엔지니어  
**내용:**
- DLQ(Dead Letter Queue) 개념
- 메시지 실패 원인
- 수동 복구 방법
- 자동 재처리 설정

**예상 시간:** 25분

---

### 6. consumer/DEPLOYMENT_CHECKLIST.md
**대상:** 배포 담당자  
**내용:**
- 배포 전 검증 항목
- 데이터베이스 마이그레이션
- 보안 검사
- 성능 테스트

**예상 시간:** 30분 + 실행 시간

---

### 7. DOCKER_OPTIMIZATION.md
**대상:** DevOps 엔지니어, 운영 담당자  
**내용:**
- Docker Compose 구성
- 리소스 최적화
- 성능 튜닝
- 환경별 설정 (개발, 스테이징, 프로덕션)

**예상 시간:** 40분

---

### 8. PRODUCTION_DEPLOYMENT.md
**대상:** 배포/릴리스 관리자  
**내용:**
- 배포 전 체크리스트 (1주일)
- 배포 당일 일정
- 무중단 배포 방법
- 긴급 롤백 절차

**예상 시간:** 45분 + 배포 시간

---

### 9. OPERATIONS_MANUAL.md
**대상:** 운영 담당자  
**내용:**
- 일일 점검 사항
- 모니터링 대시보드 설정
- 성능 최적화 팁
- 장애 대응 절차
- 주간/월간 유지보수

**예상 시간:** 60분 (초기), 10분 (일일)

---

### 10. PROJECT_README.md
**대상:** 프로젝트 관리자, 새로운 팀원  
**내용:**
- 프로젝트 전체 개요
- 모든 모듈 (consumer, backend, batch, frontend)
- 상호 연결 관계
- 의존성 맵
- 배포 플로우

**예상 시간:** 30분

---

## 🔗 주요 링크 맵

```
프로젝트 시작
    ├─→ 개발자 온보딩
    │   ├─ QUICKSTART.md (필수)
    │   ├─ PIPELINE_ARCHITECTURE.md
    │   └─ consumer/README.md
    │
    ├─→ 배포 준비
    │   ├─ DEPLOYMENT_CHECKLIST.md
    │   ├─ DOCKER_OPTIMIZATION.md
    │   └─ PRODUCTION_DEPLOYMENT.md
    │
    ├─→ 프로덕션 운영
    │   ├─ OPERATIONS_MANUAL.md
    │   ├─ DLQ_GUIDE.md
    │   └─ 모니터링 설정
    │
    └─→ 문제 해결
        ├─ DLQ_GUIDE.md (메시지 실패)
        ├─ OPERATIONS_MANUAL.md (운영 문제)
        ├─ QUICKSTART.md (설정 문제)
        └─ logs/ (application logs)
```

---

## 🎯 역할별 문서 매트릭스

| 역할 | 필수 문서 | 권장 문서 | 참고 문서 |
|------|---------|---------|---------|
| **Backend Dev** | QUICKSTART, PIPELINE | consumer/README | PROJECT_README |
| **Consumer Dev** | consumer/README, QUICKSTART | PIPELINE, DLQ_GUIDE | OPERATIONS |
| **DevOps** | DOCKER_OPTIMIZATION, PRODUCTION | OPERATIONS | DEPLOYMENT |
| **배포 담당자** | PRODUCTION, DEPLOYMENT | DOCKER_OPTIMIZATION | OPERATIONS |
| **운영 담당자** | OPERATIONS, DLQ_GUIDE | DOCKER_OPTIMIZATION | QUICKSTART |
| **QA/SQA** | SQA_ISO9001_ASSESSMENT | COMPLETION_REPORT | CI/CD 설정 |
| **새로운 팀원** | QUICKSTART, PROJECT_README | PIPELINE | consumer/README |
| **System Architect** | PIPELINE, PROJECT_README | DOCKER_OPTIMIZATION, SQA | PRODUCTION |

---

## 🎖️ 품질 & 규정 준수

### SQA & ISO 9001 평가
- **문서:** [SQA_ISO9001_ASSESSMENT.md](SQA_ISO9001_ASSESSMENT.md)
- **내용:**
  - SQA 성숙도 평가 (85/100)
  - ISO 9001 준수 현황 (75/100)
  - 강점 및 약점 분석
  - 개선 로드맵 (3개월)
  - 우선순위 액션 아이템

- **대상:** 품질 담당자, 경영진, 프로젝트 리더

---

## 📋 자주 묻는 질문 (FAQ)

### Q1: 프로젝트를 처음 시작할 때 어디서부터 봐야 하나요?
**A:** [QUICKSTART.md](consumer/QUICKSTART.md)에서 5분 만에 실행하고, [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md)에서 전체 흐름을 이해하세요.

### Q2: 메시지 처리가 실패했을 때는?
**A:** [DLQ_GUIDE.md](consumer/DLQ_GUIDE.md)를 참고하세요. 자동 재처리 또는 수동 복구 방법이 나와 있습니다.

### Q3: 프로덕션에 배포하려면?
**A:** 
1. [DEPLOYMENT_CHECKLIST.md](consumer/DEPLOYMENT_CHECKLIST.md) - 배포 전 점검
2. [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - 배포 절차
3. [OPERATIONS_MANUAL.md](OPERATIONS_MANUAL.md) - 운영 방법

### Q4: 품질 관점에서 프로젝트는 어느 정도 수준인가요?
**A:** [SQA_ISO9001_ASSESSMENT.md](SQA_ISO9001_ASSESSMENT.md)를 참고하세요.
- SQA 성숙도: 85/100 (A)
- ISO 9001 준수: 75/100 (B+)
- 강점: 자동화, 문서화, 배포 안정성
- 개선 필요: 모니터링, 메트릭 수집

### Q5: 성능 최적화는?
**A:** [DOCKER_OPTIMIZATION.md](DOCKER_OPTIMIZATION.md)에서 CPU/메모리 튜닝, Consumer 스케일링, Kafka 파티션 조정을 참고하세요.

### Q6: Consumer가 느려요. 어떻게 해야 하나요?
**A:** [OPERATIONS_MANUAL.md](OPERATIONS_MANUAL.md)의 "성능 최적화" 섹션을 참고하세요.
- Consumer 인스턴스 증가
- Kafka 파티션 증가
- 데이터베이스 인덱스 확인
- 메모리 할당 증가

### Q7: ISO 9001 인증을 받으려면?
**A:** [SQA_ISO9001_ASSESSMENT.md](SQA_ISO9001_ASSESSMENT.md)의 "ISO 9001 준수 로드맵"을 참고하세요.
- Phase 1: 품질 정책 수립 (Month 1)
- Phase 2: 운영 개선 (Month 2-3)
- Phase 3: 개선 시스템 (Month 4-6)
- Phase 4: 인증 획득 (Month 6+)

---

## 🔄 지속적인 개선

### 문서 업데이트 주기

| 문서 | 주기 | 담당자 |
|------|------|--------|
| QUICKSTART | 분기별 (3개월) | Dev Lead |
| PIPELINE_ARCHITECTURE | 변경 시 (구조 변경) | System Architect |
| OPERATIONS_MANUAL | 월간 (1개월) | Ops Lead |
| PRODUCTION_DEPLOYMENT | 변경 시 (배포 프로세스) | DevOps |
| DLQ_GUIDE | 연간 (12개월) | Senior Dev |

### 문서 기여 가이드

1. 문서에서 부정확한 부분 발견 시
   - 이슈 작성: "문서 버그: [파일명] - [설명]"
   - PR 제출 환영

2. 새로운 운영 팁 추가
   - OPERATIONS_MANUAL.md에 추가
   - 팀과 공유 (Slack)

3. 코드 변경 시
   - 관련 문서 업데이트 필수
   - PR에 문서 변경 포함

---

## 🚀 시작하기

### Step 1: 문서 읽기 순서

```bash
# 현재 위치
📁 news_pipline/

# 1단계: 5분 빠른 시작 (필수!)
읽기: consumer/QUICKSTART.md

# 2단계: 전체 이해 (20분)
읽기: PIPELINE_ARCHITECTURE.md

# 3단계: 실행 (30분)
명령어: docker-compose up -d
확인: docker-compose ps

# 4단계: 배포 (필요시)
읽기: PRODUCTION_DEPLOYMENT.md
```

### Step 2: 실제 실행

```bash
# 저장소 클론
git clone <repo-url>
cd news_pipline

# 환경 설정
cp consumer/.env.example .env
# .env 파일 수정 (API_KEY 등)

# 실행
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f consumer
```

### Step 3: 지속적인 학습

- 주간: [OPERATIONS_MANUAL.md](OPERATIONS_MANUAL.md) "주간 유지보수"
- 월간: [OPERATIONS_MANUAL.md](OPERATIONS_MANUAL.md) "월간 검토"
- 분기: 성능 분석 및 최적화

---

## 📞 도움말 & 지원

### 기술 지원
- **일반 문제:** [QUICKSTART.md#트러블슈팅](consumer/QUICKSTART.md)
- **메시지 실패:** [DLQ_GUIDE.md](consumer/DLQ_GUIDE.md)
- **운영 문제:** [OPERATIONS_MANUAL.md#트러블슈팅](OPERATIONS_MANUAL.md)
- **배포 문제:** [PRODUCTION_DEPLOYMENT.md#트러블슈팅](PRODUCTION_DEPLOYMENT.md)

### 긴급 연락처
- **On-Call 엔지니어:** [OPERATIONS_MANUAL.md#긴급_연락처](OPERATIONS_MANUAL.md)
- **Slack 채널:** #news-pipeline-alerts

### 문서 개선
- 오류 리포트: GitHub Issues
- 개선 제안: Pull Requests
- 토론: GitHub Discussions

---

## 📊 프로젝트 통계

| 항목 | 수치 |
|------|------|
| 총 문서 | 10개 |
| 총 페이지 | ~5,000줄 |
| 코드 샘플 | 100+ |
| 체크리스트 항목 | 50+ |
| 타겟 독자 | 5+ 역할 |

---

## 🎓 학습 경로

### Level 1: 기초 (1주일)
- [ ] QUICKSTART.md 완료
- [ ] docker-compose up -d 성공
- [ ] 기본 모니터링 명령어 학습

### Level 2: 중급 (2주일)
- [ ] PIPELINE_ARCHITECTURE.md 이해
- [ ] consumer 코드 리뷰
- [ ] DLQ 처리 경험

### Level 3: 고급 (1개월)
- [ ] PRODUCTION_DEPLOYMENT.md 숙지
- [ ] 배포 경험
- [ ] 성능 최적화 적용

### Level 4: 전문가 (3개월)
- [ ] 모든 문서 정통
- [ ] 자동화 스크립트 작성
- [ ] 팀 온보딩 가능

---

**마지막 업데이트:** 2026-01-02  
**다음 리뷰:** 2026-04-02 (분기별)  
**버전:** 1.0 (완성 버전)  
**상태:** ✅ 프로덕션 준비 완료
