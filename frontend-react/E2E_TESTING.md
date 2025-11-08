# E2E 테스트 가이드 (Playwright)

## 개요
Playwright를 사용한 엔드투엔드(E2E) 테스트입니다. 실제 브라우저에서 사용자 시나리오를 자동으로 테스트합니다.

## 설치 완료
- ✅ @playwright/test
- ✅ Chromium 브라우저

## 테스트 구조

```
e2e/
├── pages/                    # Page Object Model
│   ├── NewsListPage.js      # 뉴스 목록 페이지
│   ├── NewsDetailPage.js    # 뉴스 상세 페이지
│   └── LoginPage.js         # 로그인 페이지
└── tests/                   # 테스트 시나리오
    ├── news-flow.spec.js    # 뉴스 조회 플로우 (5개)
    ├── chatbot.spec.js      # 챗봇 상호작용 (3개)
    └── auth.spec.js         # 인증 플로우 (5개, 스킵됨)
```

## 실행 방법

### 1. 기본 실행 (헤드리스 모드)
```bash
npm run test:e2e
```

### 2. UI 모드 (브라우저 보면서)
```bash
npm run test:e2e:ui
```

### 3. 디버그 모드 (단계별 실행)
```bash
npm run test:e2e:debug
```

### 4. 특정 테스트만 실행
```bash
npx playwright test news-flow
npx playwright test chatbot
```

## 테스트 시나리오

### ✅ 뉴스 조회 플로우 (news-flow.spec.js)
1. **메인 페이지 뉴스 목록 확인** - 뉴스 카드가 표시되는지 확인
2. **카테고리 선택** - 경제 카테고리 선택 시 필터링 확인
3. **뉴스 상세 이동** - 카드 클릭 시 상세 페이지 이동
4. **관련 기사 표시** - 관련 뉴스가 사이드바에 표시
5. **뒤로 가기** - 뒤로 가기 버튼으로 목록 복귀

### ✅ 챗봇 상호작용 (chatbot.spec.js)
1. **챗봇 열기** - 아이콘 클릭 시 챗봇 창 표시
2. **메시지 전송** - 메시지 입력 후 전송, 응답 확인
3. **챗봇 닫기** - 닫기 버튼으로 챗봇 종료

### ⏭️ 인증 플로우 (auth.spec.js) - 스킵됨
> 실제 로그인 기능 구현 후 활성화 필요

1. 로그인 페이지 접근
2. 유효한 계정으로 로그인
3. 로그인 후 좋아요 기능
4. 로그인 후 댓글 작성
5. 로그아웃

## 설정 파일 (playwright.config.js)

```javascript
{
  testDir: './e2e/tests',          // 테스트 파일 위치
  baseURL: 'http://localhost:5173', // 개발 서버 URL
  timeout: 30000,                   // 테스트 타임아웃
  retries: CI ? 2 : 0,              // CI 환경에서 재시도
  use: {
    trace: 'on-first-retry',        // 실패 시 추적 기록
    screenshot: 'only-on-failure',  // 실패 시 스크린샷
  },
  webServer: {
    command: 'npm run dev',         // 자동으로 개발 서버 시작
    port: 5173,
  }
}
```

## 주의사항

### 1. 백엔드 서버 실행 필요
E2E 테스트는 실제 API를 호출하므로 백엔드 서버가 실행 중이어야 합니다:
```bash
# backend 디렉토리에서
docker-compose up -d
# 또는
python manage.py runserver
```

### 2. 데이터베이스 상태
- 테스트용 데이터가 DB에 있어야 합니다
- 프로덕션 DB에서 실행하지 마세요

### 3. 인증 테스트
`auth.spec.js`는 현재 스킵 상태입니다. 테스트 계정 생성 후:
```javascript
test.skip → test 로 변경
await loginPage.login('실제계정', '실제비밀번호')
```

## 테스트 결과 확인

### HTML 리포트
테스트 실행 후 자동으로 생성됩니다:
```bash
npx playwright show-report
```

### 스크린샷 & 비디오
실패한 테스트의 스크린샷과 비디오는 `test-results/` 폴더에 저장됩니다.

### Trace Viewer
상세한 디버깅 정보:
```bash
npx playwright show-trace trace.zip
```

## CI/CD 통합

### GitHub Actions 예시
```yaml
- name: Install dependencies
  run: npm ci
  
- name: Install Playwright Browsers
  run: npx playwright install --with-deps chromium
  
- name: Run E2E tests
  run: npm run test:e2e
  
- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Page Object Model (POM) 패턴

각 페이지를 클래스로 분리하여 재사용성과 유지보수성을 높였습니다:

```javascript
// 사용 예시
const newsListPage = new NewsListPage(page)
await newsListPage.goto()
await newsListPage.selectCategory('경제')
await newsListPage.clickNewsCard(0)
```

## 트러블슈팅

### 타임아웃 오류
```javascript
// playwright.config.js에서 타임아웃 증가
timeout: 60000
```

### 요소를 찾을 수 없음
```javascript
// 대기 시간 추가
await page.waitForSelector('.news-card', { timeout: 10000 })
```

### 서버 시작 실패
```javascript
// webServer.timeout 증가
webServer: {
  timeout: 120000
}
```

## 다음 단계

1. **더 많은 시나리오 추가**
   - 검색 기능 테스트
   - 무한 스크롤 테스트
   - 에러 상태 테스트

2. **비주얼 회귀 테스트**
   ```javascript
   await expect(page).toHaveScreenshot()
   ```

3. **성능 테스트**
   ```javascript
   const metrics = await page.metrics()
   ```

4. **접근성 테스트**
   ```bash
   npm install -D @axe-core/playwright
   ```
