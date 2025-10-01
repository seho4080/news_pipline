import axios from 'axios'

// 기본 API 설정
export const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 토큰 설정 함수
export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}

// 토큰 자동 설정 (앱 시작시)
const token = localStorage.getItem('access_token')
if (token) {
  setAuthToken(token)
}

// 응답 인터셉터 (토큰 만료 처리 등)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setAuthToken(null)
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api