import { useState, useEffect } from 'react'
import { PAGINATION } from '../../shared/config/constants'

// 뉴스 필터링 훅
export const useNewsFilter = (newsData) => {
  const [activeTab, setActiveTab] = useState(1) // tabs[0].id
  const [sortBy, setSortBy] = useState('latest')
  const [currentPage, setCurrentPage] = useState(1)
  const [filteredNews, setFilteredNews] = useState([])
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    if (!newsData || newsData.length === 0) return

    let filtered = []
    
    // 탭별 필터링
    if (activeTab === 1) {
      // 전체 뉴스
      filtered = newsData[0]?.[sortBy] || []
    } else {
      // 특정 카테고리
      filtered = newsData[activeTab - 1]?.[sortBy] || []
    }

    setFilteredNews(filtered)
    setTotalPages(filtered.length || 1)
    setCurrentPage(1)
  }, [newsData, activeTab, sortBy])

  const handleTabChange = (tabId) => {
    setActiveTab(tabId)
  }

  const handleSortChange = (newSort) => {
    setSortBy(newSort)
  }

  return {
    activeTab,
    sortBy,
    currentPage,
    totalPages,
    filteredNews,
    handleTabChange,
    handleSortChange,
    setCurrentPage,
  }
}

// 필터 컨트롤 컴포넌트
export const NewsFilterControls = ({ sortBy, onSortChange }) => {
  return (
    <div className="filters__container">
      <select 
        className="filters" 
        value={sortBy}
        onChange={(e) => onSortChange(e.target.value)}
      >
        <option value="latest">최신순</option>
        <option value="recommend">추천순</option>
      </select>
    </div>
  )
}