import { Link } from 'react-router-dom'
import { StateButton } from '../../shared/ui'
import { formatDate } from '../../shared/lib/utils'
import './NewsCard.scss'

const NewsCard = ({ data }) => {
  const formattedDate = formatDate(data.write_date)

  return (
    <article className="modern-news-card">
      {/* Card Image/Thumbnail Area */}
      <div className="card-media">
        <div className="media-placeholder">
          <i className="📰" />
        </div>
        <div className="category-badge">
          <StateButton type="state" size="sm" variant="category">
            {data.category}
          </StateButton>
        </div>
      </div>

      {/* Card Content */}
      <div className="card-content">
        {/* Meta Information */}
        <div className="card-meta">
          <div className="meta-left">
            <span className="author">{data.writer}</span>
            <span className="separator">•</span>
            <time className="date" dateTime={data.write_date}>
              {formattedDate}
            </time>
          </div>
          <div className="stats-mini">
            <span className="stat-item">
              <i className="❤️" />
              {data.total_like}
            </span>
            <span className="stat-item">
              <i className="👀" />
              {data.total_read}
            </span>
          </div>
        </div>

        {/* Title and Content */}
        <Link to={`/news/${data.article_id}`} className="content-link">
          <h2 className="card-title">{data.title}</h2>
          <p className="card-description">
            {data.content?.slice(0, 120)}
            {data.content?.length > 120 && '...'}
          </p>
        </Link>

        {/* Keywords Tags */}
        {data.keywords && data.keywords.length > 0 && (
          <div className="card-tags">
            {data.keywords.slice(0, 3).map((tag, index) => (
              <StateButton
                key={index}
                type="tag"
                size="xs"
                variant="outline"
              >
                #{tag}
              </StateButton>
            ))}
            {data.keywords.length > 3 && (
              <span className="tags-more">+{data.keywords.length - 3}</span>
            )}
          </div>
        )}

        {/* Card Actions */}
        <div className="card-actions">
          <div className="engagement-stats">
            <button className="engagement-btn like-btn" aria-label="좋아요">
              <i className="❤️" />
              <span>{data.total_like}</span>
            </button>
            <span className="engagement-stat">
              <i className="👀" />
              <span>{data.total_read} 읽음</span>
            </span>
          </div>
          
          <div className="action-buttons">
            {data.url && (
              <a 
                href={data.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="external-link-btn"
                aria-label="원문 보기"
              >
                <i className="🔗" />
                <span>원문</span>
              </a>
            )}
          </div>
        </div>
      </div>
    </article>
  )
}

export default NewsCard