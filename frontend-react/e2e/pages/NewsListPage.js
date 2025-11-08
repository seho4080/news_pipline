export class NewsListPage {
  constructor(page) {
    this.page = page
    this.pageTitle = page.locator('h1')
    this.newsCards = page.locator('.news-card')
    this.categoryTabs = page.locator('.tab')
    this.searchInput = page.locator('input[placeholder*="검색"]')
  }

  async goto() {
    await this.page.goto('/')
  }

  async selectCategory(category) {
    await this.page.click(`text=${category}`)
  }

  async clickNewsCard(index = 0) {
    await this.newsCards.nth(index).click()
  }

  async searchNews(query) {
    await this.searchInput.fill(query)
    await this.searchInput.press('Enter')
  }

  async getNewsCount() {
    return await this.newsCards.count()
  }

  async waitForNewsLoaded() {
    await this.page.waitForSelector('.news-card', { timeout: 10000 })
  }
}
