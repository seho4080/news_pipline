import { useState, useEffect } from 'react'
import { Bar, Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
} from 'chart.js'
import { ContentBox } from '../../shared/ui'
import { ArticlePreview } from '../../entities/news'
import { userApi } from '../../entities/user'
import { CHART_COLORS } from '../../shared/config/constants'
import './DashboardChartsWidget.scss'

ChartJS.register(
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
)

export const DashboardChartsWidget = () => {
  const [dashboardData, setDashboardData] = useState({
    categoryData: { labels: [], datasets: [{ data: [], backgroundColor: [] }] },
    keywordData: { labels: [], datasets: [{ data: [], backgroundColor: "#C7E4B8" }] },
    readData: { labels: [], datasets: [{ data: [], backgroundColor: "#DBB8E4" }] },
    categories: [],
    favoriteArticles: []
  })

  const chartOptions = {
    doughnut: {
      plugins: {
        legend: {
          display: true,
          position: "right",
          labels: { padding: 15, boxWidth: 20, font: { size: 14 } }
        },
        tooltip: {
          callbacks: {
            label: (context) => `${context.label}: ${context.raw}개`
          }
        }
      }
    },
    barHorizontal: {
      indexAxis: "y",
      scales: { x: { beginAtZero: true } },
      plugins: { legend: { display: false } }
    },
    barVertical: {
      indexAxis: "x",
      scales: { x: { beginAtZero: true } },
      plugins: { legend: { display: false } }
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [dashResponse, likesResponse] = await Promise.all([
        userApi.getDashboardData(),
        userApi.getLikedArticles()
      ])

      const { keyword_count, category_count, number_of_written_articles } = dashResponse.data
      const favoriteArticles = likesResponse.data

      const categoriesArray = Object.entries(category_count)
      const colors = categoriesArray.map((_, i) => CHART_COLORS[i % CHART_COLORS.length])

      setDashboardData({
        categoryData: {
          labels: Object.keys(category_count),
          datasets: [{ data: Object.values(category_count), backgroundColor: colors }]
        },
        keywordData: {
          labels: Object.keys(keyword_count),
          datasets: [{ data: Object.values(keyword_count), backgroundColor: "#C7E4B8" }]
        },
        readData: {
          labels: Object.keys(number_of_written_articles),
          datasets: [{ data: Object.values(number_of_written_articles), backgroundColor: "#DBB8E4" }]
        },
        categories: categoriesArray,
        favoriteArticles
      })
    } catch (error) {
      console.error('대시보드 데이터 로드 실패:', error)
    }
  }

  return (
    <div className="dashboard-charts">
      <h1 className="title">DASHBOARD</h1>
      <p className="subtitle">
        방문 기록 및 좋아요 데이터를 기반으로 나의 관심 분야를 확인하고,<br />
        관심 분야에 맞는 기사를 추천 받아보세요.
      </p>
      
      <div className="layout">
        <ContentBox className="category">
          <h1>🐤 나의 관심 카테고리</h1>
          <p className="card_description">
            내가 주로 읽은 기사들을 분석하여 정치, 경제, 문화 등 가장 관심 있는
            뉴스 카테고리를 한눈에 보여드립니다.
          </p>
          <div className="category__chart">
            <Doughnut data={dashboardData.categoryData} options={chartOptions.doughnut} />
            <div className="category__labels">
              {dashboardData.categories.map((category, index) => (
                <span
                  key={index}
                  style={{
                    borderColor: dashboardData.categoryData.datasets[0].backgroundColor[index],
                    color: dashboardData.categoryData.datasets[0].backgroundColor[index],
                  }}
                  className="category__label"
                >
                  {index + 1}순위: {category[0]} ({category[1]}개)
                </span>
              ))}
            </div>
          </div>
        </ContentBox>

        <ContentBox className="keyword">
          <h1>⭐️ 주요 키워드</h1>
          <p className="card_description">
            내가 관심있게 본 뉴스 기사들에서 가장 많이 등장한 핵심 키워드를
            추출하여 현재 나의 주요 관심사를 보여드립니다.
          </p>
          <Bar data={dashboardData.keywordData} options={chartOptions.barHorizontal} />
        </ContentBox>
      </div>
      
      <div className="layout">
        <ContentBox>
          <h1>📰 주간 읽은 기사</h1>
          <p className="card_description">
            최근 일주일 동안 하루에 몇 개의 기사를 읽었는지 그래프로 확인하며 나의
            뉴스 소비 패턴을 분석합니다.
          </p>
          <Bar data={dashboardData.readData} options={chartOptions.barVertical} />
        </ContentBox>

        <ContentBox className="like-news">
          <h1>❤️ 좋아요 누른 기사</h1>
          <p className="card_description">
            내가 좋아요를 누른 기사들의 목록을 한곳에서 모아보고 다시 찾아볼 수
            있습니다.
          </p>
          {dashboardData.favoriteArticles.map((article, index) => (
            <ArticlePreview key={index} to={`/news/${article.id}`} news={article} />
          ))}
        </ContentBox>
      </div>
    </div>
  )
}