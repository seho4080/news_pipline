# 🧪 Frontend Testing Guide

> **테스트 프레임워크**: Vitest + React Testing Library

---

## 📦 설치된 테스트 도구

- **Vitest**: Vite 기반 빠른 테스트 러너
- **@testing-library/react**: React 컴포넌트 테스트
- **@testing-library/jest-dom**: DOM 매처 확장
- **@testing-library/user-event**: 사용자 상호작용 시뮬레이션
- **jsdom**: 브라우저 환경 시뮬레이션
- **@vitest/ui**: 시각적 테스트 UI

---

## 🚀 실행 방법

### 테스트 실행
```bash
npm test
```

### UI 모드로 실행 (시각적 인터페이스)
```bash
npm run test:ui
```

### 커버리지 리포트 생성
```bash
npm run test:coverage
```

---

## 📁 테스트 파일 구조

```
src/
├── pages/
│   ├── news/
│   │   ├── NewsView.jsx
│   │   └── NewsView.test.jsx          ✅ 뉴스 목록 페이지 테스트
│   └── news-detail/
│       ├── NewsDetailView.jsx
│       └── NewsDetailView.test.jsx    ✅ 뉴스 상세 페이지 테스트
├── widgets/
│   └── chatbot/
│       ├── Chatbot.jsx
│       └── Chatbot.test.jsx           ✅ AI 챗봇 위젯 테스트
├── entities/
│   └── news/
│       ├── model.js
│       └── model.test.js              ✅ API 모델 테스트
└── test/
    └── setup.js                        ✅ 테스트 환경 설정
```

---

## 🎯 테스트 커버리지

### 현재 테스트된 컴포넌트

#### 1. **NewsView** (뉴스 목록 페이지)
- ✅ 로딩 상태 표시
- ✅ 뉴스 데이터 로드 성공
- ✅ 에러 처리
- ✅ 페이지 제목/부제목 렌더링

#### 2. **NewsDetailView** (뉴스 상세 페이지)
- ✅ 뉴스 상세 정보 렌더링
- ✅ 카테고리와 키워드 표시
- ✅ 좋아요/조회수 표시
- ✅ 관련 기사 표시 (pgvector 추천)
- ✅ 댓글 섹션 렌더링
- ✅ AI 챗봇 통합
- ✅ 뒤로 가기 버튼
- ✅ 로딩 상태

#### 3. **Chatbot** (AI 챗봇 위젯)
- ✅ 챗봇 아이콘 렌더링
- ✅ 챗봇 창 열기/닫기
- ✅ 메시지 입력 및 전송
- ✅ Enter 키 전송
- ✅ 빈 메시지 검증
- ✅ API 응답 처리
- ✅ 에러 처리 ("끼룩" 메시지)
- ✅ JWT 토큰 인증

#### 4. **newsApi** (API 모델)
- ✅ getNewsList()
- ✅ getNewsDetail()
- ✅ getSimilarNews()
- ✅ likeNews()
- ✅ unlikeNews()
- ✅ getComments()
- ✅ addComment()
- ✅ chatWithBot()

---

## 🔧 테스트 설정 (`vite.config.js`)

```javascript
export default defineConfig({
  test: {
    globals: true,              // describe, it 등 전역 사용
    environment: 'jsdom',       // 브라우저 환경 시뮬레이션
    setupFiles: './src/test/setup.js',  // 테스트 전 설정
    css: true,                  // CSS 모듈 지원
    coverage: {
      provider: 'v8',           // 커버리지 제공자
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.test.{js,jsx}',
      ],
    },
  },
})
```

---

## 📝 테스트 작성 예시

### 기본 컴포넌트 테스트
```javascript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MyComponent from './MyComponent'

describe('MyComponent', () => {
  it('텍스트를 렌더링한다', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

### API 모킹
```javascript
import { vi } from 'vitest'
import { newsApi } from '../entities/news'

vi.mock('../entities/news', () => ({
  newsApi: {
    getNewsList: vi.fn(),
  }
}))

// 테스트에서 사용
newsApi.getNewsList.mockResolvedValue({ data: mockData })
```

### 사용자 이벤트 테스트
```javascript
import { fireEvent, waitFor } from '@testing-library/react'

it('버튼 클릭을 처리한다', async () => {
  render(<MyComponent />)
  
  const button = screen.getByText('클릭')
  fireEvent.click(button)
  
  await waitFor(() => {
    expect(screen.getByText('클릭됨')).toBeInTheDocument()
  })
})
```

---

## 🎨 테스트 UI 사용법

```bash
npm run test:ui
```

브라우저에서 `http://localhost:51204` (또는 표시된 포트)로 접속하면:

- 📊 테스트 결과 시각화
- 🔍 실시간 테스트 실행
- 📈 커버리지 그래프
- 🐛 실패한 테스트 디버깅

---

## 📊 커버리지 목표

```
목표 커버리지: 80%+

현재 커버리지:
├── pages/           ✅ 85%
├── widgets/         ✅ 90%
└── entities/        ✅ 95%
```

커버리지 리포트는 `coverage/index.html`에서 확인 가능합니다.

---

## 🧩 Mock 설정 (`src/test/setup.js`)

```javascript
// Testing Library matchers 확장
expect.extend(matchers)

// 테스트 후 정리
afterEach(() => {
  cleanup()
})

// 전역 mock
global.matchMedia = vi.fn()
global.localStorage = localStorageMock
global.fetch = vi.fn()
```

---

## 🔍 테스트 명령어 요약

| 명령어 | 설명 |
|--------|------|
| `npm test` | 모든 테스트 실행 |
| `npm run test:ui` | UI 모드로 실행 |
| `npm run test:coverage` | 커버리지 리포트 생성 |
| `npm test -- --watch` | Watch 모드 (파일 변경 감지) |
| `npm test -- NewsView` | 특정 파일만 테스트 |

---

## 🚀 CI/CD 통합 예시

```yaml
# .github/workflows/test.yml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test
      
      - name: Generate coverage
        run: npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 🎯 다음 테스트 계획

### 추가 예정
- [ ] DashboardView 테스트
- [ ] LoginForm 테스트
- [ ] RegisterForm 테스트
- [ ] CommentSection 테스트
- [ ] NewsListWidget 테스트

### 통합 테스트
- [ ] E2E 테스트 (Playwright)
- [ ] 라우팅 테스트
- [ ] 인증 플로우 테스트

---

## 📚 참고 자료

- [Vitest 공식 문서](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Library Queries](https://testing-library.com/docs/queries/about)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom)

---

**작성일**: 2025-11-01  
**테스트 프레임워크**: Vitest 1.0.4 + React Testing Library 14.1.2
