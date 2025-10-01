import { useState } from 'react'
import { newsApi } from '../../entities/news'

// 좋아요 기능 훅
export const useLikeArticle = (articleId, initialLiked = false, initialCount = 0) => {
  const [liked, setLiked] = useState(initialLiked)
  const [likeCount, setLikeCount] = useState(initialCount)
  const [isAnimating, setIsAnimating] = useState(false)

  const handleLike = async () => {
    try {
      if (!liked) {
        await newsApi.likeNews(articleId)
        setLiked(true)
        setLikeCount(prev => prev + 1)
      } else {
        await newsApi.unlikeNews(articleId)
        setLiked(false)
        setLikeCount(prev => prev - 1)
      }
      
      // 애니메이션 효과
      setIsAnimating(true)
      setTimeout(() => setIsAnimating(false), 600)
    } catch (error) {
      console.error('좋아요 처리 실패:', error)
      // 실패시 원상복구
      setLiked(prev => !prev)
      setLikeCount(prev => prev + (liked ? 1 : -1))
    }
  }

  return {
    liked,
    likeCount,
    isAnimating,
    handleLike,
  }
}

// 좋아요 버튼 컴포넌트
export const LikeButton = ({ articleId, initialLiked, initialCount, className = '' }) => {
  const { liked, likeCount, isAnimating, handleLike } = useLikeArticle(articleId, initialLiked, initialCount)

  return (
    <button 
      className={`like-button ${className}`}
      onClick={handleLike}
    >
      <span>{liked ? "♥" : "♡"} {likeCount}</span>
      {isAnimating && (
        <span className="floating-heart">
          {liked ? "♥" : "♡"}
        </span>
      )}
    </button>
  )
}