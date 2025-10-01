import { useState, useEffect } from 'react'
import { ContentBox, StateButton, PaginationButton } from '../../shared/ui'
import { NewsCard } from '../../entities/news'
import { useNewsFilter, NewsFilterControls } from '../../features/filter-news/index.jsx'
import { tabs } from '../../shared/assets/data/tabs'
import './NewsListWidget.scss'

export const NewsListWidget = ({ newsData }) => {
  const {
    activeTab,
    sortBy,
    currentPage,
    totalPages,
    filteredNews,
    handleTabChange,
    handleSortChange,
    setCurrentPage,
  } = useNewsFilter(newsData)

  // 카테고리 탭은 항상 표시 (API 실패와 무관)

  // 현재 탭에 해당하는 뉴스 개수
  const currentTabData = newsData && newsData[activeTab] ? newsData[activeTab] : {}
  const totalArticles = currentTabData.rawData?.length || 0

  // 현재 페이지의 뉴스 리스트
  const currentPageNews = filteredNews.length > 0 && filteredNews[currentPage - 1] ? filteredNews[currentPage - 1] : []

  return (
    <div className="modern-news-list-widget">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            <span className="hero-icon">🤖</span>
            AI 맞춤 추천 뉴스
          </h1>
          <p className="hero-description">
            당신이 원하는 뉴스, 이제 AI가 직접 추천해드립니다!<br />
            나만의 취향을 기반으로, 맞춤형 뉴스만 쏙쏙 골라주는<br />
            뉴스 큐레이팅 서비스 <strong>SSAFYNEWS</strong>에 빠져보세요.
          </p>
          
          <div className="hero-features">
            <div className="feature-item">
              <span className="feature-icon">💬</span>
              <span>AI 챗봇과 기사 대화</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">📊</span>
              <span>뉴스 소비 패턴 분석</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🎯</span>
              <span>개인 맞춤 큐레이션</span>
            </div>
          </div>
        </div>
      </section>

      {/* Category Tabs */}
      <section className="category-section">
        <div className="category-header">
          <h2>카테고리별 뉴스</h2>
          <div className="category-stats">
            <span className="stat-badge">
              총 <strong>{totalArticles}</strong>개 기사
            </span>
          </div>
        </div>
        
        <div className="category-tabs">
          {tabs.map((tab) => (
            <StateButton
              key={tab.id}
              type="state"
              size="md"
              isActive={activeTab === tab.id}
              onClick={() => handleTabChange(tab.id)}
              className="category-tab"
            >
              {tab.label}
            </StateButton>
          ))}
        </div>
      </section>
      
      {/* News Content */}
      <section className="news-content-section">
        <div className="content-header">
          <div className="content-info">
            <h3 className="section-title">
              {tabs.find(tab => tab.id === activeTab)?.label || '전체'} 뉴스
            </h3>
            <p className="content-count">
              {currentPageNews.length}개의 기사 (페이지 {currentPage}/{totalPages})
            </p>
          </div>
          
          <div className="content-controls">
            <NewsFilterControls 
              sortBy={sortBy} 
              onSortChange={handleSortChange}
              className="filter-controls"
            />
          </div>
        </div>

        {/* News Grid */}
        {currentPageNews.length > 0 ? (
          <div className="news-grid">
            {currentPageNews.map((news) => (
              <div key={news.article_id} className="news-grid-item">
                <NewsCard data={news} />
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-content">
              <div className="empty-icon">📰</div>
              <h3>{tabs.find(tab => tab.id === activeTab)?.label || '전체'} 뉴스</h3>
              <p>백엔드 서버 연결 후 {tabs.find(tab => tab.id === activeTab)?.label || '전체'} 카테고리의 뉴스가 여기에 표시됩니다.</p>
              <div className="demo-info">
                <p>🔧 <strong>개발 모드:</strong> 카테고리 탭 기능이 정상 작동 중</p>
                <p>📡 백엔드 API: <code>http://localhost:8000/api</code></p>
              </div>
            </div>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="pagination-section">
            <PaginationButton 
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
            />
          </div>
        )}
      </section>
    </div>
  )
}