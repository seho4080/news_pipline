import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import NewsView from './NewsView'
import { newsApi } from '../../entities/news'

// newsApi mock
vi.mock('../../entities/news', () => ({
  newsApi: {
    getNewsList: vi.fn(),
  }
}))

// tabs mock
vi.mock('../../shared/assets/data/tabs', () => ({
  tabs: [
    { id: 0, name: '전체' },
    { id: 1, name: '연예' },
    { id: 2, name: '경제' },
  ]
}))

describe('NewsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('로딩 중일 때 로딩 스피너를 표시한다', () => {
    newsApi.getNewsList.mockImplementation(() => new Promise(() => {}))
    
    render(
      <BrowserRouter>
        <NewsView />
      </BrowserRouter>
    )
    
    expect(screen.getByText(/최신 뉴스를 불러오고 있습니다/i)).toBeInTheDocument()
  })

  it('뉴스 데이터를 성공적으로 로드한다', async () => {
    const mockNewsData = {
      '연예': [
        {
          article_id: 1,
          title: '테스트 연예 뉴스',
          writer: '기자',
          write_date: '2025-01-01',
          category: '연예',
          content: '테스트 내용',
          url: 'http://test.com',
          keywords: ['키워드1', '키워드2'],
          total_like: 10,
          total_read: 100,
          is_like: false,
        }
      ],
      '경제': [
        {
          article_id: 2,
          title: '테스트 경제 뉴스',
          writer: '기자',
          write_date: '2025-01-01',
          category: '경제',
          content: '테스트 내용',
          url: 'http://test2.com',
          keywords: ['경제', '주식'],
          total_like: 5,
          total_read: 50,
          is_like: false,
        }
      ]
    }

    newsApi.getNewsList.mockResolvedValue({ data: mockNewsData })
    
    render(
      <BrowserRouter>
        <NewsView />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText('📰 뉴스 센터')).toBeInTheDocument()
    })
  })

  it('에러 발생 시 에러 메시지를 표시한다', async () => {
    newsApi.getNewsList.mockRejectedValue(new Error('API 에러'))
    
    render(
      <BrowserRouter>
        <NewsView />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText(/뉴스 데이터 연결 실패/i)).toBeInTheDocument()
    })
  })

  it('페이지 제목과 부제목을 렌더링한다', async () => {
    newsApi.getNewsList.mockResolvedValue({ data: {} })
    
    render(
      <BrowserRouter>
        <NewsView />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText('📰 뉴스 센터')).toBeInTheDocument()
      expect(screen.getByText(/실시간으로 업데이트되는/i)).toBeInTheDocument()
    })
  })
})
