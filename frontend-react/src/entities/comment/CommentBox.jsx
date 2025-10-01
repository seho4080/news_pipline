import { formatDate } from '../../shared/lib/utils'
import './CommentBox.scss'

const CommentBox = ({ data, onDelete }) => {
  const handleDeleteButton = () => {
    // 미구현
    if (onDelete) {
      onDelete(data.id)
    }
  }

  return (
    <article className="comment">
      <div className="comment__header">
        <span className="comment__header-author">{data.username}</span>
        <span className="comment__header-date">
          {formatDate(data.created_at)}
        </span>
        <button className="comment-delete-button" onClick={handleDeleteButton}>
          ×
        </button>
      </div>
      <p className="comment__content">{data.content}</p>
    </article>
  )
}

export default CommentBox