# SSAFY NEWS - React Version

Vue 프로젝트를 React로 마이그레이션한 버전입니다.

## 프로젝트 구조

```
frontend-react/
├── public/                 # 정적 파일들 (이미지, favicon 등)
├── src/
│   ├── components/         # 재사용 가능한 컴포넌트
│   │   ├── TheHeader.jsx
│   │   ├── TheFooter.jsx
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   └── ProtectedRoute.jsx
│   ├── views/             # 페이지 컴포넌트
│   │   ├── NewsView.jsx
│   │   ├── NewsDetailView.jsx
│   │   ├── DashBoardView.jsx
│   │   └── NotFoundView.jsx
│   ├── hooks/             # 커스텀 React 훅
│   ├── utils/             # 유틸리티 함수
│   ├── assets/            # 스타일시트, 이미지 등
│   ├── App.jsx            # 메인 App 컴포넌트
│   └── main.jsx           # 진입점
├── package.json
└── README.md
```

## 설치 및 실행

### 1. 의존성 설치
```bash
npm install
```

### 2. 개발 서버 실행
```bash
npm run dev
```

서버가 시작되면 http://localhost:5173 에서 애플리케이션을 확인할 수 있습니다.

### 3. 빌드
```bash
npm run build
```

## 주요 특징

- **React 18** + **Vite** 사용
- **React Router v6** 를 통한 라우팅
- **SCSS** 지원
- **Axios** 를 통한 API 통신
- **Chart.js** 차트 라이브러리 지원
- JWT 토큰 기반 인증 시스템

## 🎉 마이그레이션 100% 완료!

✅ **Vue 3 → React 18** 완전 변환  
✅ **Vue Router → React Router v6** 변환  
✅ **Pinia 상태관리 → React Hooks** 변환  
✅ **모든 Vue 컴포넌트 → React 함수형 컴포넌트** 변환  
✅ **SCSS 스타일링** 완전 유지  
✅ **정적 자산** 모두 이동  
✅ **라우팅 및 인증 가드** 완전 구현  
✅ **Chart.js 대시보드** 완전 구현  
✅ **실시간 댓글 및 챗봇** 완전 구현  
✅ **API 연동** 모든 기능 완료

## ✅ 완료된 추가 기능들

- ✅ 실제 API 연동 완료 (뉴스 목록, 상세, 댓글, 좋아요, 챗봇)
- ✅ Chart.js 컴포넌트 완전 구현 (도넛차트, 막대차트)
- ✅ 모든 UI/UX 컴포넌트 변환 완료 (NewsCard, ArticlePreview, CommentBox 등)
- ✅ Chatbot 컴포넌트 완전 변환
- ✅ 반응형 디자인 적용 완료
- ✅ JWT 인증 시스템 완전 구현
- ✅ 페이지네이션 및 필터링 완료

## 비교: Vue vs React

| 기능 | Vue | React |
|------|-----|-------|
| 라우팅 | Vue Router | React Router |
| 상태관리 | Pinia | useState/useContext |
| 컴포넌트 | SFC (.vue) | JSX (.jsx) |
| 스타일링 | Scoped CSS | CSS Modules/SCSS |
| 빌드도구 | Vite | Vite |

## 개발 가이드

### 컴포넌트 생성
```jsx
import { useState, useEffect } from 'react'
import './Component.scss'

const MyComponent = ({ prop1, prop2 }) => {
  const [state, setState] = useState('')

  useEffect(() => {
    // 컴포넌트 마운트 시 실행
  }, [])

  return (
    <div className="my-component">
      {/* JSX 내용 */}
    </div>
  )
}

export default MyComponent
```

### API 호출
```jsx
import axios from 'axios'

const fetchData = async () => {
  try {
    const response = await axios.get('/api/endpoint')
    return response.data
  } catch (error) {
    console.error('API Error:', error)
    throw error
  }
}
```+ Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
