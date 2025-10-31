import { describe, it, expect, vi } from 'vitest'
import { newsApi } from './model'
import api from '../../shared/api/base'

// base api mock
vi.mock('../../shared/api/base', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}))

describe('newsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getNewsList', () => {
    it('뉴스 목록을 가져온다', async () => {
      const mockData = { '연예': [], '경제': [] }
      api.get.mockResolvedValue(mockData)
      
      const result = await newsApi.getNewsList()
      
      expect(api.get).toHaveBeenCalledWith('/news/')
      expect(result).toEqual(mockData)
    })
  })

  describe('getNewsDetail', () => {
    it('특정 뉴스의 상세 정보를 가져온다', async () => {
      const mockArticle = { article_id: 1, title: '테스트' }
      api.get.mockResolvedValue(mockArticle)
      
      const result = await newsApi.getNewsDetail(1)
      
      expect(api.get).toHaveBeenCalledWith('/news/1/')
      expect(result).toEqual(mockArticle)
    })
  })

  describe('getSimilarNews', () => {
    it('유사한 뉴스를 가져온다', async () => {
      const mockSimilar = { article_list: [] }
      api.get.mockResolvedValue(mockSimilar)
      
      const result = await newsApi.getSimilarNews(1)
      
      expect(api.get).toHaveBeenCalledWith('/news/1/similar/')
      expect(result).toEqual(mockSimilar)
    })
  })

  describe('likeNews', () => {
    it('뉴스에 좋아요를 추가한다', async () => {
      const mockResponse = { message: '좋아요 등록' }
      api.put.mockResolvedValue(mockResponse)
      
      const result = await newsApi.likeNews(1)
      
      expect(api.put).toHaveBeenCalledWith('/news/1/likes/')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('unlikeNews', () => {
    it('뉴스 좋아요를 취소한다', async () => {
      const mockResponse = { message: '좋아요 취소' }
      api.delete.mockResolvedValue(mockResponse)
      
      const result = await newsApi.unlikeNews(1)
      
      expect(api.delete).toHaveBeenCalledWith('/news/1/likes/')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getComments', () => {
    it('뉴스의 댓글 목록을 가져온다', async () => {
      const mockComments = [{ id: 1, content: '댓글' }]
      api.get.mockResolvedValue(mockComments)
      
      const result = await newsApi.getComments(1)
      
      expect(api.get).toHaveBeenCalledWith('/news/comment/1/')
      expect(result).toEqual(mockComments)
    })
  })

  describe('addComment', () => {
    it('새 댓글을 추가한다', async () => {
      const mockComment = { id: 1, content: '새 댓글' }
      api.post.mockResolvedValue(mockComment)
      
      const result = await newsApi.addComment(1, '새 댓글')
      
      expect(api.post).toHaveBeenCalledWith('/news/comment/1/', { content: '새 댓글' })
      expect(result).toEqual(mockComment)
    })
  })

  describe('chatWithBot', () => {
    it('챗봇과 대화한다', async () => {
      const mockResponse = { message: '답변입니다' }
      api.post.mockResolvedValue(mockResponse)
      
      const result = await newsApi.chatWithBot(1, '질문입니다')
      
      expect(api.post).toHaveBeenCalledWith('/news/1/chat/', { message: '질문입니다' })
      expect(result).toEqual(mockResponse)
    })
  })
})
