import { useState } from 'react'
import { newsApi } from '../../entities/news'

// 댓글 추가 훅
export const useAddComment = (articleId, onCommentAdded) => {
  const [comment, setComment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const addComment = async () => {
    const content = comment.trim()
    if (!content || isSubmitting) return

    setIsSubmitting(true)
    try {
      const newComment = await newsApi.addComment(articleId, content)
      setComment('')
      if (onCommentAdded) {
        onCommentAdded(newComment.data)
      }
    } catch (error) {
      console.error('댓글 작성 실패:', error)
      alert('댓글 작성에 실패했습니다.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return {
    comment,
    setComment,
    addComment,
    isSubmitting,
  }
}

// 댓글 추가 컴포넌트
export const AddCommentForm = ({ articleId, onCommentAdded }) => {
  const { comment, setComment, addComment, isSubmitting } = useAddComment(articleId, onCommentAdded)

  return (
    <div className="add-comment-container">
      <div className="comment-input">
        <textarea 
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="댓글 추가..." 
          className="comment-box" 
          rows="1"
          disabled={isSubmitting}
        />
      </div>
      <div className="add-comment-button-container">
        <button 
          className="btn-comment" 
          disabled={!comment.trim() || isSubmitting} 
          onClick={addComment}
        >
          {isSubmitting ? '작성중...' : '댓글'}
        </button>
      </div>
    </div>
  )
}