import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ContentBox, StateButton } from '../../shared/ui'
import { NewsModel, newsApi } from '../../entities/news'
import { CommentSectionWidget } from '../../widgets'
import { ChatbotWidget } from '../../widgets'
import { useLikeArticle } from '../../features/like-article/index.jsx'
import { formatDate } from '../../shared/lib/utils'
import './NewsDetailView.scss'

const NewsDetailView = () => {
  const { id: articleId } = useParams()
  const navigate = useNavigate()
  const [news, setNews] = useState(null)
  const [relatedNews, setRelatedNews] = useState([])
  const [loading, setLoading] = useState(true)
  
  const { liked, likeCount, handleLike } = useLikeArticle(news?.article_id, news?.is_like, news?.total_like)

  const loadNewsDetail = async () => {
    try {
      setLoading(true)
      const [newsDetail, similar] = await Promise.all([
        newsApi.getNewsDetail(articleId),
        newsApi.getSimilarNews(articleId)
      ])
      
      setNews(newsDetail.data)
      setRelatedNews(similar.data.article_list || [])
    } catch (error) {
      console.error('뉴스 상세 정보 로드 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (articleId) {
      loadNewsDetail()
    }
  }, [articleId])

  if (loading) {
    return <div>뉴스를 불러오는 중...</div>
  }

  if (!news) {
    return <div>뉴스를 찾을 수 없습니다.</div>
  }

  return (
    <>
      <button onClick={() => navigate(-1)} className="back-btn">
        ← 뒤로 가기
      </button>
      
      <div className="news-detail">
        <div className="article__container">
          <ContentBox>
            <div className="article">
              <div className="article__header">
                <StateButton type="state" size="sm" isActive disabled>
                  {news?.category}
                </StateButton>
                <h2 className="article__header-title">{news?.title}</h2>
                <div className="article__header-writer">
                  <span>{news.writer}</span>
                  <span> 🕒 {formatDate(news.write_date)}</span>
                </div>
              </div>

              <p className="article__content">{news?.content}</p>

              <div className="article__tags">
                {news.keywords?.map((tag, index) => (
                  <StateButton
                    key={index}
                    type="tag"
                    size="sm"
                  >
                    {tag}
                  </StateButton>
                ))}
              </div>

              <div className="article__content__footer">
                <div className="article__content__emoji">
                  <span className="emoji-btn">
                    <span>{liked ? ' ❤️ ' : '🤍'}</span>{likeCount}
                  </span>
                  <div className="emoji-btn">
                    <span className="content__emoji-eye"> 👀 </span>
                    {news?.total_read}
                  </div>
                  <a href={news.url} target="_blank" rel="noopener noreferrer">📄</a>
                </div>
                <button className="emoji-btn" onClick={handleLike}>
                  <span>{liked ? "❤️" : "🤍"} 좋아요</span>
                </button>
              </div>
            </div>
          </ContentBox>
          
          <CommentSectionWidget articleId={articleId} />
        </div>

        <ContentBox className="sidebar">
          <h1 className="sidebar__title">📰 관련 기사</h1>
          {relatedNews.map((newsItem, index) => (
            <div key={index} className="related-news-item">
              <a href={`/news/${newsItem.article_id}`} className="related-news-link">
                <h4>{newsItem.title}</h4>
                <p>{newsItem.writer} • {formatDate(newsItem.write_date)}</p>
              </a>
            </div>
          ))}
        </ContentBox>
        
        <ChatbotWidget articleId={parseInt(articleId)} />
      </div>
    </>
  )
}

export default NewsDetailView