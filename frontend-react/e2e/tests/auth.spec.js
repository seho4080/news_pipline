import { test, expect } from '@playwright/test'
import { LoginPage } from '../pages/LoginPage'
import { NewsDetailPage } from '../pages/NewsDetailPage'

test.describe('인증 플로우', () => {
  test.skip('로그인 페이지에 접근할 수 있다', async ({ page }) => {
    const loginPage = new LoginPage(page)
    
    await loginPage.goto()
    
    await expect(loginPage.usernameInput).toBeVisible()
    await expect(loginPage.passwordInput).toBeVisible()
    await expect(loginPage.loginButton).toBeVisible()
  })

  test.skip('유효한 계정으로 로그인할 수 있다', async ({ page }) => {
    const loginPage = new LoginPage(page)
    
    await loginPage.goto()
    
    // 테스트 계정으로 로그인 (실제 환경에 맞게 수정 필요)
    await loginPage.login('testuser', 'testpass123')
    
    // 로그인 성공 확인
    await expect(page).toHaveURL('/')
    const isLoggedIn = await loginPage.isLoggedIn()
    expect(isLoggedIn).toBeTruthy()
  })

  test.skip('로그인 후 좋아요를 누를 수 있다', async ({ page }) => {
    const loginPage = new LoginPage(page)
    const newsDetailPage = new NewsDetailPage(page)
    
    // 로그인
    await loginPage.goto()
    await loginPage.login('testuser', 'testpass123')
    
    // 뉴스 상세 페이지로 이동
    await newsDetailPage.goto(1)
    await newsDetailPage.waitForContentLoaded()
    
    // 좋아요 버튼 클릭
    await newsDetailPage.clickLike()
    
    // 좋아요 상태 확인 (하트 색상 변경 등)
    await expect(page.locator('button:has-text("좋아요")')).toHaveClass(/liked|active/)
  })

  test.skip('로그인 후 댓글을 작성할 수 있다', async ({ page }) => {
    const loginPage = new LoginPage(page)
    const newsDetailPage = new NewsDetailPage(page)
    
    // 로그인
    await loginPage.goto()
    await loginPage.login('testuser', 'testpass123')
    
    // 뉴스 상세 페이지로 이동
    await newsDetailPage.goto(1)
    await newsDetailPage.waitForContentLoaded()
    
    // 댓글 작성
    const testComment = '테스트 댓글입니다'
    await newsDetailPage.addComment(testComment)
    
    // 댓글이 표시되는지 확인
    await expect(page.locator(`text=${testComment}`)).toBeVisible({ timeout: 5000 })
  })

  test.skip('로그아웃할 수 있다', async ({ page }) => {
    const loginPage = new LoginPage(page)
    
    // 로그인
    await loginPage.goto()
    await loginPage.login('testuser', 'testpass123')
    
    // 로그아웃
    await loginPage.logout()
    
    // 로그아웃 확인
    const isLoggedIn = await loginPage.isLoggedIn()
    expect(isLoggedIn).toBeFalsy()
  })
})
