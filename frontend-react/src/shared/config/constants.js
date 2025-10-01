export const API_BASE_URL = 'http://localhost:8000/api'

export const ROUTES = {
  HOME: '/',
  NEWS: '/news',
  NEWS_DETAIL: '/news/:id',
  DASHBOARD: '/dashboard',
  LOGIN: '/login',
  REGISTER: '/register',
}

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
}

export const PAGINATION = {
  ITEMS_PER_PAGE: 10,
}

export const CHART_COLORS = [
  '#FF6B6B', // Tomato Red
  '#FFC300', // Saffron
  '#6BCB77', // Mint Green
  '#4D96FF', // Dodger Blue
  '#845EC2', // Purple
  '#FF9671', // Coral
  '#00C9A7', // Turquoise
  '#C34A36', // Brick Red
  '#F9F871', // Lemon
  '#2C73D2', // Royal Blue
]