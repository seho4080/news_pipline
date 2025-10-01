import { Link } from 'react-router-dom'
import { ContentBox, StateButton } from '../../shared/ui'
import { formatDate } from '../../shared/lib/utils'
import './ArticlePreview.scss'

const ArticlePreview = ({ news, to }) => {
  const hasInteraction = news.article_interaction && !!news.article_interaction

  const Component = to ? Link : 'div'
  const componentProps = to ? { to } : {}

  return (
    <Component {...componentProps}>
      <ContentBox>
        <div className="top">
          <h1>{news.title}</h1>
        </div>
        <div className="bottom">
          <div>
            <StateButton type="tag" size="sm">
              {news.writer}
            </StateButton>
            {formatDate(new Date(news.write_date))}
          </div>

          {hasInteraction && (
            <div className="bottom__icons">
              <div>
                ❤️ {news.total_like}
              </div>
              <div>
                👀 {news.total_read}
              </div>
            </div>
          )}
        </div>
      </ContentBox>
    </Component>
  )
}

export default ArticlePreview