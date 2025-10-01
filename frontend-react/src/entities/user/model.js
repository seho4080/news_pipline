import api from '../../shared/api/base'

// 사용자 API
export const userApi = {
  // 로그인
  login: (credentials) => api.post('/members/login/', credentials),
  
  // 회원가입
  signup: (userData) => api.post('/members/signup/', userData),
  
  // 좋아요한 기사 목록
  getLikedArticles: () => api.get('/members/likes/'),
  
  // 대시보드 데이터  
  getDashboardData: () => api.get('/members/dashboard/'),
  
  // 좋아요한 기사 목록 (별칭)
  getFavoriteArticles: () => api.get('/members/likes/'),
}

// 사용자 모델
export class UserModel {
  constructor(data = {}) {
    this.username = data.username || ''
    this.email = data.email || ''
    this.isAuthenticated = !!localStorage.getItem('access_token')
  }
  
  // 로그인 처리
  login(tokens) {
    localStorage.setItem('access_token', tokens.access)
    localStorage.setItem('refresh_token', tokens.refresh)
    this.isAuthenticated = true
  }
  
  // 로그아웃 처리
  logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    this.isAuthenticated = false
  }
}