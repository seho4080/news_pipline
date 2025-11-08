import { test, expect } from '@playwright/test'
import { NewsDetailPage } from '../pages/NewsDetailPage'

test.describe('챗봇 상호작용', () => {
  test('챗봇 아이콘을 클릭하면 챗봇이 열린다', async ({ page }) => {
    const newsDetailPage = new NewsDetailPage(page)
    
    await newsDetailPage.goto(1)
    await newsDetailPage.waitForContentLoaded()
    
    // 챗봇 열기
    await newsDetailPage.openChatbot()
    
    // 챗봇 창이 표시되는지 확인
    await expect(page.locator('text=AI 비서 소봇')).toBeVisible()
    await expect(newsDetailPage.chatbotInput).toBeVisible()
  })

  test('챗봇에 메시지를 전송할 수 있다', async ({ page }) => {
    const newsDetailPage = new NewsDetailPage(page)
    
    await newsDetailPage.goto(1)
    await newsDetailPage.waitForContentLoaded()
    
    // 챗봇 열기
    await newsDetailPage.openChatbot()
    await page.waitForTimeout(500)
    
    // 메시지 전송
    const testMessage = '이 뉴스에 대해 설명해줘'
    await newsDetailPage.sendChatMessage(testMessage)
    
    // 사용자 메시지가 표시되는지 확인
    await expect(page.locator(`.chatbot-message.user:has-text("${testMessage}")`)).toBeVisible()
    
    // 봇 응답 대기 (최대 10초)
    await expect(page.locator('.chatbot-message.bot').last()).toBeVisible({ timeout: 10000 })
  })

  test('챗봇 닫기 버튼으로 챗봇을 닫을 수 있다', async ({ page }) => {
    const newsDetailPage = new NewsDetailPage(page)
    
    await newsDetailPage.goto(1)
    await newsDetailPage.waitForContentLoaded()
    
    // 챗봇 열기
    await newsDetailPage.openChatbot()
    await expect(page.locator('text=AI 비서 소봇')).toBeVisible()
    
    // 닫기 버튼 클릭
    await page.click('button.close-btn')
    
    // 챗봇이 닫혔는지 확인
    await expect(page.locator('.chatbot-bubble')).not.toBeVisible()
  })
})
