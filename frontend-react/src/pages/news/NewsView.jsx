import { useState, useEffect } from 'react'
import { NewsListWidget } from '../../widgets'
import { newsApi } from '../../entities/news'
import { PAGINATION } from '../../shared/config/constants'
import './NewsView.scss'

const NewsView = () => {
  const [newsData, setNewsData] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const processNewsData = (rawData) => {
    console.log('===== 백엔드 응답 rawData =====', rawData)
    console.log('rawData 타입:', typeof rawData)
    console.log('rawData 키 목록:', Object.keys(rawData))
    console.log('rawData 키 개수:', Object.keys(rawData).length)
    
    const { tabs } = require('../../shared/assets/data/tabs')
    console.log('tabs 길이:', tabs.length)
    
    const initialNewsData = Array.from({ length: tabs.length }, () => ({
      rawData: [],
      latest: [],
      recommend: [],
      totalPageValue: 0
    }))
    console.log('initialNewsData 길이:', initialNewsData.length)

    const keys = Object.keys(rawData)
    console.log('처리할 키들:', keys)

    // 키워드 별 기사 처리 로직
    keys.forEach((key, idx) => {
      console.log(`\n--- 처리 중: key=${key}, idx=${idx} ---`)
      const items = rawData[key]
      console.log(`${key} 기사 개수:`, items.length)
      console.log(`접근할 배열 인덱스: initialNewsData[${idx + 1}]`)
      console.log(`배열 범위 체크: ${idx + 1} < ${initialNewsData.length} = ${idx + 1 < initialNewsData.length}`)
      
      // 안전 검사: initialNewsData 범위 확인
      if (idx + 1 >= initialNewsData.length) {
        console.error(`❌ Index out of bounds: ${idx + 1} for key: ${key}`)
        return
      }

      items.forEach(item => {
        initialNewsData[0].rawData.push(item)
        initialNewsData[idx + 1].rawData.push(item)
      })

      const latest = [...initialNewsData[idx + 1].rawData].sort((a, b) => b.write_date - a.write_date)
      const recommend = [...initialNewsData[idx + 1].rawData].sort((a, b) => b.total_like - a.total_like)

      // 페이지네이션 처리
      const latestChunk = []
      const recommendChunk = []

      for (let i = 0; i < latest.length; i += PAGINATION.ITEMS_PER_PAGE) {
        latestChunk.push(latest.slice(i, i + PAGINATION.ITEMS_PER_PAGE))
      }

      for (let i = 0; i < recommend.length; i += PAGINATION.ITEMS_PER_PAGE) {
        recommendChunk.push(recommend.slice(i, i + PAGINATION.ITEMS_PER_PAGE))
      }

      initialNewsData[idx + 1].latest = latestChunk
      initialNewsData[idx + 1].recommend = recommendChunk
      initialNewsData[idx + 1].totalPageValue = latestChunk.length
    })

    console.log('\n===== 처리 완료된 initialNewsData =====')
    console.log('전체 기사 수:', initialNewsData[0].rawData.length)
    initialNewsData.forEach((data, idx) => {
      if (idx > 0 && data.rawData.length > 0) {
        console.log(`카테고리 ${idx}: ${data.rawData.length}개 기사`)
      }
    })

    // 전체 기사 처리
    const allLatest = [...initialNewsData[0].rawData].sort((a, b) => b.write_date - a.write_date)
    const allRecommend = [...initialNewsData[0].rawData].sort((a, b) => b.total_like - a.total_like)

    const allLatestChunk = []
    const allRecommendChunk = []

    for (let i = 0; i < allLatest.length; i += PAGINATION.ITEMS_PER_PAGE) {
      allLatestChunk.push(allLatest.slice(i, i + PAGINATION.ITEMS_PER_PAGE))
    }

    for (let i = 0; i < allRecommend.length; i += PAGINATION.ITEMS_PER_PAGE) {
      allRecommendChunk.push(allRecommend.slice(i, i + PAGINATION.ITEMS_PER_PAGE))
    }

    initialNewsData[0].latest = allLatestChunk
    initialNewsData[0].recommend = allRecommendChunk
    initialNewsData[0].totalPageValue = allLatestChunk.length

    return initialNewsData
  }

  useEffect(() => {
    const loadNews = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await newsApi.getNewsList()
        
        // total_count 추출
        const { total_count, ...newsCategories } = response.data
        setTotalCount(total_count || 0)
        
        const processedData = processNewsData(newsCategories)
        setNewsData(processedData)
      } catch (error) {
        console.error('뉴스 데이터 로드 실패:', error)
        setError('뉴스 데이터를 불러오는데 실패했습니다.')
      } finally {
        setLoading(false)
      }
    }

    loadNews()
  }, [])

  // 로딩 중이거나 에러가 있어도 카테고리는 표시
  const mockNewsData = [
    {
      rawData: [],
      latest: [],
      recommend: [],
      totalPageValue: 0
    },
    // 빈 데이터로 카테고리별 초기화
    ...Array(17).fill(0).map(() => ({
      rawData: [],
      latest: [],
      recommend: [],
      totalPageValue: 0
    }))
  ]

  const displayNewsData = newsData.length > 0 ? newsData : mockNewsData

  if (loading) {
    return (
      <div className="modern-news-page">
        <div className="page-container">
          <header className="page-header">
            <div className="header-content">
              <h1 className="page-title">📰 뉴스 센터</h1>
              <p className="page-subtitle">
                실시간으로 업데이트되는 최신 뉴스와 인사이트를 만나보세요
              </p>
            </div>
          </header>
          
          <main className="page-main">
            <NewsListWidget newsData={displayNewsData} />
            <div className="loading-overlay">
              <div className="loading-spinner">
                <div className="spinner"></div>
                <h3>최신 뉴스를 불러오고 있습니다...</h3>
                <p>잠시만 기다려주세요</p>
              </div>
            </div>
          </main>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="modern-news-page">
        <div className="page-container">
          <header className="page-header">
            <div className="header-content">
              <h1 className="page-title">📰 뉴스 센터</h1>
              <p className="page-subtitle">
                실시간으로 업데이트되는 최신 뉴스와 인사이트를 만나보세요
              </p>
            </div>
          </header>
          
          <main className="page-main">
            <NewsListWidget newsData={displayNewsData} />
            <div className="error-overlay">
              <div className="error-content">
                <div className="error-icon">⚠️</div>
                <h3>뉴스 데이터 연결 실패</h3>
                <p>{error}</p>
                <p>카테고리는 정상 작동하며, 백엔드 연결 후 뉴스가 표시됩니다.</p>
                <button 
                  className="retry-btn"
                  onClick={() => window.location.reload()}
                >
                  다시 시도
                </button>
              </div>
            </div>
          </main>
        </div>
      </div>
    )
  }

  return (
    <div className="modern-news-page">
      <div className="page-container">
        <header className="page-header">
          <div className="header-content">
            <h1 className="page-title">📰 뉴스 센터</h1>
            <p className="page-subtitle">
              실시간으로 업데이트되는 최신 뉴스와 인사이트를 만나보세요
            </p>
          </div>
        </header>
        
        <main className="page-main">
          <NewsListWidget newsData={newsData} totalCount={totalCount} />
        </main>
      </div>
    </div>
  )
}

export default NewsView