import { useState, useEffect } from 'react'
import { ContentBox } from '../../shared/ui'
import { CommentBox } from '../../entities/comment'
import { AddCommentForm } from '../../features/add-comment/index.jsx'
import { newsApi } from '../../entities/news'

export const CommentSectionWidget = ({ articleId }) => {
  const [comments, setComments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (articleId) {
      loadComments()
    }
  }, [articleId])

  const loadComments = async () => {
    try {
      setLoading(true)
      const response = await newsApi.getComments(articleId)
      setComments(response.data)
    } catch (error) {
      console.error('댓글 로드 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCommentAdded = (newComment) => {
    setComments(prev => [newComment, ...prev])
  }

  if (loading) {
    return <div>댓글을 불러오는 중...</div>
  }

  return (
    <ContentBox>
      <AddCommentForm 
        articleId={articleId} 
        onCommentAdded={handleCommentAdded}
      />
      
      {comments && comments.length > 0 ? (
        <div>
          {comments.map((comment, index) => (
            <CommentBox key={index} data={comment} />
          ))}
        </div>
      ) : (
        <div className="no-comment">
          <h4>아직 댓글이 없습니다.</h4>
        </div>
      )}
    </ContentBox>
  )
}