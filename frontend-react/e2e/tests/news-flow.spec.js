import { test, expect } from '@playwright/test'
import { NewsListPage } from '../pages/NewsListPage'
import { NewsDetailPage } from '../pages/NewsDetailPage'

test.describe('뉴스 조회 플로우', () => {
  test('메인 페이지에서 뉴스 목록을 확인할 수 있다', async ({ page }) => {
    const newsListPage = new NewsListPage(page)
    
    await newsListPage.goto()
    await newsListPage.waitForNewsLoaded()
    
    const newsCount = await newsListPage.getNewsCount()
    expect(newsCount).toBeGreaterThan(0)
    
    await expect(newsListPage.pageTitle).toBeVisible()
  })

  test('카테고리를 선택하면 해당 뉴스가 표시된다', async ({ page }) => {
    const newsListPage = new NewsListPage(page)
    
    await newsListPage.goto()
    await newsListPage.waitForNewsLoaded()
    
    // 경제 카테고리 선택
    await newsListPage.selectCategory('경제')
    await page.waitForTimeout(1000) // API 응답 대기
    
    const newsCount = await newsListPage.getNewsCount()
    expect(newsCount).toBeGreaterThan(0)
  })

  test('뉴스를 클릭하면 상세 페이지로 이동한다', async ({ page }) => {
    const newsListPage = new NewsListPage(page)
    const newsDetailPage = new NewsDetailPage(page)
    
    await newsListPage.goto()
    await newsListPage.waitForNewsLoaded()
    
    // 첫 번째 뉴스 클릭
    await newsListPage.clickNewsCard(0)
    
    // 상세 페이지로 이동 확인
    await newsDetailPage.waitForContentLoaded()
    await expect(newsDetailPage.newsTitle).toBeVisible()
    await expect(newsDetailPage.newsContent).toBeVisible()
  })

  test('상세 페이지에서 관련 기사가 표시된다', async ({ page }) => {
    const newsDetailPage = new NewsDetailPage(page)
    
    await newsDetailPage.goto(1)
    await newsDetailPage.waitForContentLoaded()
    
    const relatedCount = await newsDetailPage.getRelatedNewsCount()
    expect(relatedCount).toBeGreaterThan(0)
  })

  test('뒤로 가기 버튼으로 목록으로 돌아갈 수 있다', async ({ page }) => {
    const newsListPage = new NewsListPage(page)
    const newsDetailPage = new NewsDetailPage(page)
    
    await newsDetailPage.goto(1)
    await newsDetailPage.waitForContentLoaded()
    
    await newsDetailPage.goBack()
    
    // 목록 페이지로 돌아왔는지 확인
    await newsListPage.waitForNewsLoaded()
    await expect(newsListPage.pageTitle).toBeVisible()
  })
})
