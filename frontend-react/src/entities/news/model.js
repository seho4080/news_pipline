import api from '../../shared/api/base'

// 뉴스 API
export const newsApi = {
  // 뉴스 목록 조회
  getNewsList: () => api.get('/news/'),
  
  // 뉴스 상세 조회
  getNewsDetail: (id) => api.get(`/news/${id}/`),
  
  // 유사 뉴스 조회
  getSimilarNews: (id) => api.get(`/news/${id}/similar/`),
  
  // 좋아요 추가
  likeNews: (id) => api.put(`/news/${id}/likes/`),
  
  // 좋아요 삭제
  unlikeNews: (id) => api.delete(`/news/${id}/likes/`),
  
  // 뉴스 댓글 조회
  getComments: (id) => api.get(`/news/comment/${id}/`),
  
  // 댓글 작성
  addComment: (id, content) => api.post(`/news/comment/${id}/`, { content }),
  
  // 챗봇 대화
  chatWithBot: (id, message) => api.post(`/news/${id}/chat/`, { message }),
}

// 뉴스 데이터 모델
export class NewsModel {
  constructor(data) {
    this.id = data.article_id
    this.title = data.title
    this.content = data.content
    this.writer = data.writer
    this.category = data.category
    this.writeDate = data.write_date
    this.totalLike = data.total_like
    this.totalRead = data.total_read
    this.keywords = data.keywords || []
    this.url = data.url
    this.isLike = data.is_like || false
  }
  
  // 간단한 요약 텍스트
  get summary() {
    return this.content.slice(0, 100) + '...'
  }
  
  // 좋아요 토글
  toggleLike() {
    this.isLike = !this.isLike
    this.totalLike += this.isLike ? 1 : -1
  }
}