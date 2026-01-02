# 🔧 Jenkins CI/CD 설정 가이드

**Jenkins를 이용한 자동화된 CI/CD 파이프라인 구성 가이드**

---

## 📋 사전 요구사항

### Jenkins 서버
- Jenkins 2.387+ (LTS)
- 최소 8GB RAM, 2 CPU
- 50GB 디스크 공간

### 설치된 플러그인
```
필수:
- Pipeline (Declarative & Scripted)
- GitHub Integration
- Docker Pipeline
- Credentials Binding
- Email Extension
- Slack Notification
- JUnit Plugin
- Code Coverage API
- Email Notification

추천:
- Blue Ocean (시각화)
- AnsiColor (로그 색상)
- Log Parser (로그 분석)
- Timestamper (타임스탬프)
```

---

## 🚀 Jenkins 설치 & 설정

### 1단계: Jenkins 설치

#### Docker를 이용한 설치 (권장)

```bash
# Jenkins 데이터 디렉토리 생성
mkdir -p ~/jenkins_data
chmod 777 ~/jenkins_data

# Jenkins Docker 컨테이너 실행
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -p 50000:50000 \
  -v ~/jenkins_data:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e JAVA_OPTS="-Xmx2g -XX:+UseG1GC" \
  jenkins/jenkins:lts-jdk11

# 로그 확인
docker logs jenkins

# 초기 Admin 토큰 확인
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

#### Linux에 직접 설치

```bash
# Ubuntu/Debian
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.03.27.key | sudo tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null

echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

sudo apt-get update
sudo apt-get install jenkins

# 시작
sudo systemctl start jenkins
sudo systemctl enable jenkins

# 초기 Admin 토큰
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

### 2단계: 웹 UI 접속

```
http://localhost:8080
```

1. 초기 Admin 토큰 입력
2. 플러그인 선택 (위의 필수/추천 플러그인)
3. Admin 계정 생성
4. Jenkins URL 설정

---

## 🔐 Credentials 설정

### 1. GitHub Token

**Jenkins UI:**
1. Manage Jenkins → Manage Credentials
2. Credentials → System → Global credentials
3. Add Credentials 클릭
4. Kind: **Username with password**
   - Username: `github_token`
   - Password: [GitHub Personal Access Token]
   - ID: `github-credentials`

### 2. Docker Registry

```
Kind: Username with password
Username: docker-registry-username
Password: docker-registry-password
ID: docker-registry-credentials
```

### 3. SSH Key (배포용)

```
Kind: SSH Username with private key
Username: deploy
Private Key: (자신의 프라이빗 키)
ID: ssh-deploy-key
```

### 4. Slack Webhook

```
Kind: Secret text
Secret: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
ID: slack-webhook
```

---

## 📝 Pipeline Job 생성

### 1단계: New Item 생성

**Jenkins Home → New Item**

```
Item name: news-pipeline
Type: Pipeline
OK 클릭
```

### 2단계: Pipeline 설정

**Pipeline 섹션:**

```
Definition: Pipeline script from SCM
SCM: Git
Repository URL: https://github.com/your-org/news_pipline.git
Credentials: github-credentials
Branch: */main, */develop
Script Path: Jenkinsfile
```

### 3단계: Trigger 설정

**Build Triggers:**

```
☑ GitHub hook trigger for GITscm polling
  (GitHub에서 push 이벤트 시 자동 빌드)

또는

☑ Poll SCM
  Schedule: H H * * * (매일 한 번)
```

---

## 🔗 GitHub 통합

### GitHub Webhook 설정

**GitHub Repository Settings → Webhooks**

1. Add webhook 클릭
2. Payload URL: `http://your-jenkins-url/github-webhook/`
3. Content type: `application/json`
4. Events: `Push events` 선택
5. Add webhook

### GitHub Personal Access Token 생성

**GitHub Settings → Developer settings → Personal access tokens**

1. Generate new token
2. Scopes: `repo`, `admin:repo_hook`
3. Token 복사해서 Jenkins Credentials에 저장

---

## 🚦 Pipeline 실행

### 수동 실행

**Jenkins Dashboard → news-pipeline → Build Now**

### 파라미터와 함께 실행

```bash
curl -X POST \
  -H "Authorization: Basic $(echo -n 'user:token' | base64)" \
  http://localhost:8080/job/news-pipeline/buildWithParameters \
  -d "ENVIRONMENT=staging&SKIP_TESTS=false&FORCE_DEPLOY=false"
```

---

## 📊 Pipeline Stages 상세

### 1. Checkout
```
Git 저장소에서 코드 다운로드
```

### 2. Code Quality Analysis (병렬)
```
Consumer:
  - pylint: Python 코드 품질
  - flake8: 스타일 검사
  - bandit: 보안 취약점

Backend:
  - pylint: Django 코드 품질
  - flake8: 스타일 검사
  - Django system check

Frontend:
  - ESLint: JavaScript 린팅
  - Type check: TypeScript 타입 확인
  - Build: Vite 빌드
```

### 3. Unit Tests (병렬)
```
Consumer: pytest with coverage
Backend: Django test suite
Frontend: Jest tests
```

### 4. Security Scan (병렬)
```
SAST: Bandit, Safety
Dependency Check: pip-audit, npm audit
```

### 5. Docker Build
```
- news-consumer:BUILD_NUMBER
- news-backend:BUILD_NUMBER
- news-frontend:BUILD_NUMBER
```

### 6. Container Security Scan
```
Trivy로 Docker 이미지 스캔
```

### 7. Push to Registry
```
Docker 이미지를 레지스트리에 푸시
(main/develop 브랜치만)
```

### 8. Deploy to Staging
```
- Staging 서버에 배포
- Health check 수행
(staging 파라미터 또는 develop 브랜치)
```

### 9. Production Approval
```
프로덕션 배포 전 승인 대기
(devops-team 멤버만 승인 가능)
```

### 10. Deploy to Production (Blue-Green)
```
- Blue 환경 유지
- Green 환경에 새 버전 배포
- Health check 후 트래픽 전환
- 문제 시 자동 롤백
```

### 11. Smoke Tests
```
- API 헬스 체크
- 기본 엔드포인트 테스트
- Frontend 로드 확인
```

---

## 🔔 알림 설정

### Slack 통지

Jenkinsfile에 이미 포함되어 있습니다:

```groovy
post {
    success {
        // 성공 메시지
    }
    failure {
        // 실패 메시지
    }
}
```

### 메일 알림

**Manage Jenkins → Configure System → Email Notification**

```
SMTP server: smtp.gmail.com
SMTP port: 587
Default user e-mail suffix: @company.com
Use SMTP Authentication: ☑
User name: your-email@gmail.com
Password: [App Password]
Use TLS: ☑
```

---

## 📈 모니터링 & 보고

### Build History 확인

```
Jenkins Dashboard → news-pipeline
- 빌드 번호 클릭
- Console Output: 실시간 로그
- Artifacts: 생성된 파일들
```

### Reports 확인

```
1. Code Coverage: 테스트 커버리지
2. Test Results: 테스트 결과
3. Lint Reports: 코드 품질
4. Security Reports: 보안 스캔 결과
```

### Blue Ocean 시각화

```
URL: http://localhost:8080/blue/

장점:
- 직관적인 파이프라인 시각화
- 각 stage의 실행 시간 표시
- 병렬 실행 상태 확인
```

---

## 🔧 환경 변수 설정

### 1. Global Properties

**Manage Jenkins → Configure System → Global properties**

```
Build environment properties:
DOCKER_REGISTRY = docker.company.com
SLACK_CHANNEL = #news-pipeline
STAGING_HOST = staging.company.com
PROD_HOST = prod.company.com
```

### 2. Credentials in Pipeline

```groovy
environment {
    REGISTRY = credentials('docker-registry-url')
    SLACK_WEBHOOK = credentials('slack-webhook')
    SSH_KEY = credentials('ssh-deploy-key')
}
```

---

## 🚀 배포 전략

### Staging 배포

```groovy
stage('Deploy to Staging') {
    when {
        expression { 
            return env.ENVIRONMENT == 'staging' || env.BRANCH_NAME == 'develop'
        }
    }
    // docker-compose로 배포
}
```

### Production Blue-Green 배포

```groovy
stage('Deploy to Production (Blue-Green)') {
    steps {
        script {
            // 1. Green 환경에 새 버전 배포
            // 2. 헬스 체크
            // 3. 트래픽 전환 (로드 밸런서)
            // 4. Blue 환경 종료
            // 5. 문제 시 자동 롤백
        }
    }
}
```

---

## 🆘 트러블슈팅

### 1. Pipeline 시작 안 됨

```bash
# Jenkins 로그 확인
docker logs jenkins

# 또는
sudo tail -f /var/log/jenkins/jenkins.log

# 문제:
# - GitHub webhook 연결 실패 → GitHub credentials 확인
# - SCM path 오류 → Jenkinsfile 경로 확인
# - 플러그인 누락 → 필수 플러그인 설치 확인
```

### 2. Docker 빌드 실패

```bash
# Docker daemon 연결 확인
docker ps

# Jenkins 컨테이너인 경우
docker exec jenkins docker ps

# 해결:
# - Docker socket 마운트 확인
# - 권한 확인 (jenkins 사용자의 docker 그룹)
```

### 3. 배포 실패

```bash
# SSH 연결 확인
ssh -i deploy_key deploy@staging-host "echo OK"

# 해결:
# - SSH 키 확인
# - 호스트 등록 (known_hosts)
# - 배포 대상 서버의 docker-compose 설정 확인
```

### 4. 병렬 실행 문제

```groovy
// 병렬 실행 문제시 maxBuilds 제한
options {
    buildDiscarder(logRotator(numToKeepStr: '10'))
    disableConcurrentBuilds()  // 순차 실행만 허용
    timeout(time: 1, unit: 'HOURS')
}
```

---

## 📚 추가 설정

### Pipeline Timeout 조정

```groovy
options {
    timeout(time: 2, unit: 'HOURS')  // 2시간으로 증가
}
```

### Artifact 보관

```groovy
post {
    always {
        archiveArtifacts artifacts: '**/*.log,**/coverage.xml'
        cleanWs()  // 작업 디렉토리 정리
    }
}
```

### Retry 로직

```groovy
stages {
    stage('Deploy') {
        steps {
            retry(3) {  // 최대 3회 재시도
                sh './deploy.sh'
            }
        }
    }
}
```

---

## 🎯 Best Practices

### 1. 작은 단계로 나누기
```
각 stage는 하나의 책임만 가지도록
```

### 2. 병렬 처리 활용
```groovy
parallel {
    stage('A') { steps { sh 'task-a' } }
    stage('B') { steps { sh 'task-b' } }
}
```

### 3. 조건부 실행
```groovy
when {
    expression { return env.BRANCH_NAME == 'main' }
}
```

### 4. 에러 처리
```groovy
post {
    always { /* 항상 실행 */ }
    success { /* 성공시만 */ }
    failure { /* 실패시만 */ }
}
```

---

## 📊 모니터링 대시보드

### 추천 플러그인
- **Prometheus Metrics Plugin**
- **Metrics**: Jenkins 성능 메트릭
- **Log Parser**: 빌드 로그 분석

### Metrics 수집

```
http://localhost:8080/prometheus/metrics

메트릭:
- jenkins_builds_total
- jenkins_build_duration_seconds
- jenkins_build_success_count
```

---

## 🔄 CI/CD Flow

```
GitHub Push
    ↓
GitHub Webhook 
    ↓
Jenkins Pipeline Start
    ↓
├── Checkout
├── Code Quality (병렬)
├── Tests (병렬)
├── Security Scan (병렬)
├── Docker Build
├── Container Scan
├── Push to Registry
├── Deploy to Staging
├── (Manual Approval for Production)
├── Deploy to Production (Blue-Green)
├── Smoke Tests
    ↓
Build Success/Failure
    ↓
Slack/Email Notification
```

---

## 📞 도움말

### Jenkins 공식 문서
- https://www.jenkins.io/doc/

### Pipeline 문법
- https://www.jenkins.io/doc/book/pipeline/

### 플러그인
- https://plugins.jenkins.io/

---

**마지막 업데이트:** 2026-01-02  
**버전:** 1.0  
**상태:** ✅ 프로덕션 준비 완료
