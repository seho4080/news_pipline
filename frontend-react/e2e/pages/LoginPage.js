export class LoginPage {
  constructor(page) {
    this.page = page
    this.usernameInput = page.locator('input[name="username"]')
    this.passwordInput = page.locator('input[name="password"]')
    this.loginButton = page.locator('button:has-text("로그인")')
    this.logoutButton = page.locator('button:has-text("로그아웃")')
    this.registerLink = page.locator('a:has-text("회원가입")')
  }

  async goto() {
    await this.page.goto('/login')
  }

  async login(username, password) {
    await this.usernameInput.fill(username)
    await this.passwordInput.fill(password)
    await this.loginButton.click()
  }

  async logout() {
    await this.logoutButton.click()
  }

  async isLoggedIn() {
    return await this.logoutButton.isVisible()
  }

  async goToRegister() {
    await this.registerLink.click()
  }
}
