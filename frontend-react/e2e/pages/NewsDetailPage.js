export class NewsDetailPage {
  constructor(page) {
    this.page = page
    this.newsTitle = page.locator('.article__header-title')
    this.newsContent = page.locator('.article__content')
    this.likeButton = page.locator('button:has-text("좋아요")')
    this.commentSection = page.locator('.comment-section')
    this.commentInput = page.locator('textarea[placeholder*="댓글"]')
    this.chatbotIcon = page.locator('img[alt="Chatbot"]')
    this.chatbotInput = page.locator('input[placeholder*="메시지"]')
    this.backButton = page.locator('button:has-text("뒤로")')
    this.relatedNews = page.locator('.related-news-item')
  }

  async goto(articleId) {
    await this.page.goto(`/news/${articleId}`)
  }

  async clickLike() {
    await this.likeButton.click()
  }

  async addComment(text) {
    await this.commentInput.fill(text)
    await this.commentInput.press('Enter')
  }

  async openChatbot() {
    await this.chatbotIcon.click()
  }

  async sendChatMessage(message) {
    await this.chatbotInput.fill(message)
    await this.page.click('button:has-text("전송")')
  }

  async goBack() {
    await this.backButton.click()
  }

  async getRelatedNewsCount() {
    return await this.relatedNews.count()
  }

  async waitForContentLoaded() {
    await this.page.waitForSelector('.article__content', { timeout: 10000 })
  }
}
