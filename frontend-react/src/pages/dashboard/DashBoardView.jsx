import { useState, useEffect } from 'react'
import { ContentBox } from '../../shared/ui'
import { userApi } from '../../entities/user'
import { DashboardChartsWidget } from "../../widgets";
import './DashBoardView.scss'

const DashBoardView = () => {
  const [dashboardData, setDashboardData] = useState(null)
  const [favoriteArticles, setFavoriteArticles] = useState([])
  const [loading, setLoading] = useState(true)

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      const [dashboard, favorites] = await Promise.all([
        userApi.getDashboardData(),
        userApi.getFavoriteArticles()
      ])
      
      setDashboardData(dashboard.data)
      setFavoriteArticles(favorites.data)
    } catch (error) {
      console.error('대시보드 데이터 로드 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  if (loading) {
    return <div>대시보드를 불러오는 중...</div>
  }

  return (
    <div className="dashboard">
      <h1 className="title">DASHBOARD</h1>
      <p className="subtitle">
        <br />방문 기록 및 좋아요 데이터를 기반으로 나의 관심 분야를 확인하고,
        <br />관심 분야에 맞는 기사를 추천 받아보세요. <br />여러분의 취업 여정의
        로드맵을 제공합니다.
      </p>
      
      <DashboardChartsWidget 
        dashboardData={dashboardData}
        favoriteArticles={favoriteArticles}
      />
    </div>
  )
}

export default DashBoardView