import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter, Routes, Route, useParams } from 'react-router-dom'
import NewsDetailView from './NewsDetailView'
import { newsApi } from '../../entities/news'

// useParams mock
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: vi.fn(),
  }
})

// newsApi mock
vi.mock('../../entities/news', () => ({
  newsApi: {
    getNewsDetail: vi.fn(),
    getSimilarNews: vi.fn(),
  },
  NewsModel: vi.fn(),
}))

// useLikeArticle mock
vi.mock('../../features/like-article/index.jsx', () => ({
  useLikeArticle: () => ({
    liked: false,
    likeCount: 10,
    handleLike: vi.fn(),
  })
}))

// widgets mock
vi.mock('../../widgets', () => ({
  CommentSectionWidget: () => <div>댓글 섹션</div>,
  ChatbotWidget: () => <div>챗봇 위젯</div>,
}))

describe('NewsDetailView', () => {
  const mockArticle = {
    article_id: 1,
    title: '테스트 뉴스 제목',
    writer: '테스트 기자',
    write_date: '2025-01-01T10:00:00',
    category: '경제',
    content: '이것은 테스트 뉴스 내용입니다.',
    url: 'http://test.com',
    keywords: ['키워드1', '키워드2', '키워드3'],
    total_like: 10,
    total_read: 100,
    is_like: false,
  }

  const mockSimilarNews = {
    article_list: [
      {
        article_id: 2,
        title: '관련 뉴스 1',
        writer: '기자',
        write_date: '2025-01-02',
      },
      {
        article_id: 3,
        title: '관련 뉴스 2',
        writer: '기자',
        write_date: '2025-01-03',
      }
    ]
  }

  beforeEach(() => {
    vi.clearAllMocks()
    useParams.mockReturnValue({ id: '1' })
    newsApi.getNewsDetail.mockResolvedValue({ data: mockArticle })
    newsApi.getSimilarNews.mockResolvedValue({ data: mockSimilarNews })
  })

  it('뉴스 상세 정보를 렌더링한다', async () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<NewsDetailView />} />
        </Routes>
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('테스트 뉴스 제목')).toBeInTheDocument()
      expect(screen.getByText('테스트 기자')).toBeInTheDocument()
      expect(screen.getByText(/이것은 테스트 뉴스 내용입니다/)).toBeInTheDocument()
    })
  })

  it('카테고리와 키워드를 표시한다', async () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<NewsDetailView />} />
        </Routes>
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('경제')).toBeInTheDocument()
      expect(screen.getByText('키워드1')).toBeInTheDocument()
      expect(screen.getByText('키워드2')).toBeInTheDocument()
      expect(screen.getByText('키워드3')).toBeInTheDocument()
    })
  })

  it('좋아요 수와 조회수를 표시한다', async () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<NewsDetailView />} />
        </Routes>
      </BrowserRouter>
    )

    await waitFor(() => {
      const likeElements = screen.getAllByText(/10/)
      const readElements = screen.getAllByText(/100/)
      expect(likeElements.length).toBeGreaterThan(0)
      expect(readElements.length).toBeGreaterThan(0)
    })
  })

  it('관련 기사를 표시한다', async () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<NewsDetailView />} />
        </Routes>
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('📰 관련 기사')).toBeInTheDocument()
      expect(screen.getByText('관련 뉴스 1')).toBeInTheDocument()
      expect(screen.getByText('관련 뉴스 2')).toBeInTheDocument()
    })
  })

  it('댓글 섹션과 챗봇을 렌더링한다', async () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<NewsDetailView />} />
        </Routes>
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('댓글 섹션')).toBeInTheDocument()
      expect(screen.getByText('챗봇 위젯')).toBeInTheDocument()
    })
  })

  it('뒤로 가기 버튼을 렌더링한다', async () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<NewsDetailView />} />
        </Routes>
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('← 뒤로 가기')).toBeInTheDocument()
    })
  })

  it('로딩 중일 때 로딩 메시지를 표시한다', () => {
    newsApi.getNewsDetail.mockImplementation(() => new Promise(() => {}))
    
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<NewsDetailView />} />
        </Routes>
      </BrowserRouter>
    )

    expect(screen.getByText(/뉴스를 불러오는 중/i)).toBeInTheDocument()
  })
})
