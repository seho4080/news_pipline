# ⚖️ CI/CD 도구 비교: Jenkins vs GitHub Actions

**뉴스 파이프라인 프로젝트에서 선택할 수 있는 두 가지 CI/CD 솔루션 비교**

---

## 📊 한눈에 비교

| 항목 | Jenkins | GitHub Actions |
|------|---------|---|
| **구축** | 자체 호스팅 필수 | GitHub 기본 제공 |
| **초기 비용** | 높음 (서버) | 무료 (월 2000분) |
| **학습곡선** | 가파름 | 완만함 |
| **커스터마이징** | 매우 높음 | 중간 정도 |
| **확장성** | 무한 | GitHub 에코시스템 내 |
| **보안** | 높음 (격리) | 높음 (GitHub 관리) |
| **커뮤니티** | 매우 큼 | 빠르게 성장 중 |
| **기업 지원** | CloudBees | Microsoft |

---

## 🏗️ 아키텍처 비교

### Jenkins

```
┌─────────────────────────────────────┐
│      자신의 서버/VM                   │
├─────────────────────────────────────┤
│  Jenkins Master (오케스트레이션)     │
│  ├─ Job 관리                        │
│  ├─ Credentials 저장                │
│  └─ UI/API 제공                     │
├─────────────────────────────────────┤
│  Jenkins Agents (실행 노드) 1~∞     │
│  ├─ Pipeline 실행                   │
│  ├─ Docker build                    │
│  └─ 배포 수행                       │
└─────────────────────────────────────┘
         ↕ (통신)
    GitHub Repository
```

### GitHub Actions

```
┌─────────────────────────────────┐
│    GitHub 클라우드               │
├─────────────────────────────────┤
│  Workflow (*.yml)               │
│  ├─ 트리거 정의                  │
│  ├─ Jobs 정의                    │
│  └─ Steps 정의                   │
├─────────────────────────────────┤
│  GitHub-hosted Runners          │
│  (Ubuntu, Windows, macOS)        │
│  또는                            │
│  Self-hosted Runners            │
└─────────────────────────────────┘
         ↕ (GitHub API)
    GitHub Repository
```

---

## ✅ Jenkins의 장점

### 1. 완전한 제어
```
✓ 자신의 서버에서 실행
✓ 모든 구성을 커스터마이징 가능
✓ 내부 네트워크에서 배포 가능
✓ 데이터가 자신의 서버에 저장됨
```

### 2. 확장성
```
✓ Agent 추가로 무한 확장
✓ 1000+ 플러그인 지원
✓ 복잡한 워크플로우 지원
✓ 여러 프로젝트 중앙 관리
```

### 3. 보안
```
✓ Credentials를 자신의 서버에 보관
✓ 격리된 실행 환경
✓ LDAP/Active Directory 통합
✓ Role-Based Access Control (RBAC)
```

### 4. 비용 (대규모)
```
✓ 초기 비용 후 무제한 빌드
✓ 월 사용량 걱정 없음
✓ 고성능 agent 구축 가능
```

### 5. 엔터프라이즈
```
✓ Declarative/Scripted Pipeline
✓ Blue Ocean (UI)
✓ CloudBees 지원
✓ Enterprise Plugin 지원
```

---

## ❌ Jenkins의 단점

### 1. 운영 복잡성
```
✗ 자체 서버 유지보수 필수
✗ 업그레이드/패치 관리
✗ 플러그인 호환성 관리
✗ 24/7 모니터링 필요
```

### 2. 초기 비용
```
✗ 서버 구매/렌탈 비용
✗ Jenkins 설치 및 설정
✗ Agent 서버 비용
✗ 전문가 채용
```

### 3. 복잡한 설정
```
✗ UI 학습 곡선 가파름
✗ Groovy 스크립트 학습 필요
✗ 플러그인 의존성 관리
✗ 설정 실수 위험 높음
```

---

## ✅ GitHub Actions의 장점

### 1. 사용 편의성
```
✓ GitHub 저장소와 네이티브 통합
✓ YAML 문법 (배우기 쉬움)
✓ Web UI로 직관적 설정
✓ 다양한 공식 액션 제공
```

### 2. 낮은 초기 비용
```
✓ GitHub 계정만 있으면 무료
✓ 월 2000분 무료 (개인)
✓ 서버 구축 불필요
✓ 5GB 아티팩트 스토리지 무료
```

### 3. 관리 용이성
```
✓ GitHub에서 모든 것 관리
✓ 자동 업그레이드
✓ 버전 관리 (Git)
✓ 회수 기능으로 롤백 가능
```

### 4. 모던 기능
```
✓ Matrix builds (조합 테스트)
✓ 환경 변수 구조화
✓ Artifact 관리 간편
✓ 로그 검색 기능
```

### 5. 보안 (작은 팀)
```
✓ GitHub에서 보안 관리
✓ Secrets 암호화
✓ Dependabot 통합
✓ 자동 보안 패치
```

---

## ❌ GitHub Actions의 단점

### 1. 제어 제한
```
✗ GitHub에서 호스팅
✗ 내부 네트워크 접근 어려움
✗ 일부 기능 제한
✗ 데이터가 GitHub에 저장됨
```

### 2. 비용 (대규모)
```
✗ 초과 사용 시 비용 발생
✗ 월 2000분 초과시 $0.008/분
✗ 대규모 팀은 비용 상승
✗ Self-hosted runner 관리 필요
```

### 3. 제한사항
```
✗ 동시 실행 제한 (계획에 따라)
✗ 최대 6시간 job 제한
✗ 외부 저장소 제한
✗ Runner 사양 고정
```

### 4. 의존성
```
✗ GitHub 상태에 의존
✗ 마이그레이션 어려움
✗ Marketplace action 품질 편차
✗ Microsoft 정책 변경 위험
```

---

## 🎯 선택 기준

### ✅ Jenkins를 선택해야 할 때

```
1. 엔터프라이즈 환경
   - 높은 보안 요구
   - 데이터 주권 필수
   - 복잡한 요구사항

2. 비용 고려
   - 대규모 팀 (100명+)
   - 무한 빌드 필요
   - 오래 운영할 계획

3. 커스터마이징
   - 매우 복잡한 워크플로우
   - 여러 프로젝트 통합 필요
   - 레거시 시스템 연동

4. 운영 가능성
   - DevOps 팀이 있음
   - 서버 관리 경험 있음
   - 24/7 모니터링 가능
```

### ✅ GitHub Actions를 선택해야 할 때

```
1. 스타트업/소규모팀
   - 초기 자금 부족
   - 빠른 출시 필요
   - 확장은 나중에

2. 단순한 워크플로우
   - 테스트 → 빌드 → 배포
   - 표준적인 CI/CD
   - 특수한 요구사항 없음

3. GitHub 헤비 유저
   - 이미 GitHub 사용 중
   - GitHub Enterprise 사용
   - 에코시스템 활용

4. 관리 최소화
   - 운영팀 작음
   - 클라우드 선호
   - 간편함 최우선
```

---

## 💰 비용 비교 (연간)

### 시나리오 1: 작은 팀 (2명, 일일 10회 빌드)

**GitHub Actions**
```
월 빌드 = 10회 × 30일 × 5분 = 1,500분
비용 = 무료 (2,000분 이내)
연간: $0
```

**Jenkins**
```
서버: AWS EC2 t3.medium = $30/월
Agent: 0개 (마스터만)
관리: 자체 (비용 미포함)
연간: $360
```

**결론: GitHub Actions 압승**

---

### 시나리오 2: 중간 팀 (10명, 일일 50회 빌드)

**GitHub Actions**
```
월 빌드 = 50회 × 30일 × 5분 = 7,500분
초과분 = 5,500분
비용 = 5,500분 × $0.008 = $44/월
연간: $528
```

**Jenkins**
```
마스터 서버: EC2 t3.large = $60/월
Agent 서버 2개: t3.medium = $60/월
관리: 1명 (부분) = $30,000/년
연간: $31,920
```

**결론: GitHub Actions 압승**

---

### 시나리오 3: 대규모 팀 (50명, 일일 200회 빌드)

**GitHub Actions**
```
월 빌드 = 200회 × 30일 × 5분 = 30,000분
초과분 = 28,000분
비용 = 28,000분 × $0.008 = $224/월
연간: $2,688
```

**Jenkins**
```
마스터 서버: EC2 c5.2xlarge = $200/월
Agent 서버 10개: c5.xlarge = $400/월
관리: 2명 = $150,000/년
연간: $157,200
```

**결론: GitHub Actions 대승**

---

## 🔄 마이그레이션

### Jenkins → GitHub Actions

```bash
# 1. GitHub Actions 문법으로 변환
Jenkinsfile → .github/workflows/*.yml

# 2. Credentials 이전
Jenkins Credentials → GitHub Secrets

# 3. 플러그인 대체
Jenkins Plugin → GitHub Action

# 4. 테스트
로컬/staging에서 검증

# 5. 전환
기존 Jenkins 비활성화
```

**시간:** 1-2주 (중소 프로젝트)

### GitHub Actions → Jenkins

```bash
# 1. Jenkinsfile 작성
.github/workflows/*.yml → Jenkinsfile

# 2. Jenkins 서버 구축
설치, 플러그인 설치, 설정

# 3. 마이그레이션
Pipeline job 생성

# 4. 테스트
모든 시나리오 검증

# 5. 전환
GitHub webhook 제거
```

**시간:** 2-4주 (인프라 구축 포함)

---

## 🎯 뉴스 파이프라인 프로젝트 추천

### 현재 상황
```
- 엔터프라이즈 규모
- 높은 보안 요구
- 복잡한 배포 (Blue-Green)
- 자체 인프라 소유
```

### 추천: **Jenkins**

**이유:**
1. ✅ 강력한 커스터마이징 (Blue-Green 배포)
2. ✅ 보안 요구사항 충족
3. ✅ 고성능 agent 구축 가능
4. ✅ 전사 CI/CD 통합

### 대안: **GitHub Actions + Self-hosted Runners**

```yaml
# .github/workflows/deploy.yml
runs-on: [self-hosted, production]
# 프라이빗 네트워크 내 runner 사용
```

---

## 📝 결론

### Jenkins 추천 환경
```
엔터프라이즈 + 복잡한 요구 + 높은 보안
→ Jenkins는 필수 선택
```

### GitHub Actions 추천 환경
```
스타트업/스몰팀 + 단순한 워크플로우
→ GitHub Actions 최적화
```

### 하이브리드 접근
```
주 배포: Jenkins (on-premise)
테스트 CI: GitHub Actions
모니터링: 둘 다 사용
```

---

## 🔗 참고

- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Jenkins vs GitHub Actions Comparison](https://www.jenkins.io/doc/book/pipeline/)

---

**마지막 업데이트:** 2026-01-02  
**버전:** 1.0  
**상태:** ✅ 완료
