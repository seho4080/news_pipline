import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import axios from 'axios'
import './TheHeader.scss'

const TheHeader = () => {
  const [isLogin, setIsLogin] = useState(false)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    setIsLogin(!!token)
  }, [location])

  const logout = () => {
    localStorage.removeItem("access_token")
    setIsLogin(false)
    delete axios.defaults.headers.common['Authorization']
    navigate("/")
    setIsMenuOpen(false)
  }

  const refreshPage = (event) => {
    event.preventDefault()
    navigate("/")
    window.location.reload()
  }

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen)
  }

  const closeMenu = () => {
    setIsMenuOpen(false)
  }

  return (
    <header className="modern-header">
      <div className="header-container">
        <div className="header-brand">
          <Link to="/" onClick={refreshPage} className="brand-link">
            <div className="logo">
              <span className="logo-icon">📰</span>
              <span className="logo-text">SSAFY NEWS</span>
            </div>
          </Link>
        </div>

        {/* Desktop Navigation */}
        <nav className="desktop-nav">
          <Link 
            to="/news" 
            className={`nav-link ${location.pathname === '/news' || location.pathname === '/' ? 'active' : ''}`}
            onClick={closeMenu}
          >
            <span className="nav-icon">🎯</span>
            뉴스 큐레이팅
          </Link>
          <Link 
            to="/dashboard"
            className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}
            onClick={closeMenu}
          >
            <span className="nav-icon">📊</span>
            대시보드
          </Link>
          {isLogin ? (
            <button className="nav-button logout-btn" onClick={logout}>
              <span className="nav-icon">👋</span>
              로그아웃
            </button>
          ) : (
            <Link 
              to="/login"
              className="nav-link login-btn"
              onClick={closeMenu}
            >
              <span className="nav-icon">🔐</span>
              로그인
            </Link>
          )}
        </nav>

        {/* Mobile Menu Button */}
        <button 
          className={`mobile-menu-btn ${isMenuOpen ? 'active' : ''}`}
          onClick={toggleMenu}
          aria-label="메뉴 토글"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        {/* Mobile Navigation */}
        <nav className={`mobile-nav ${isMenuOpen ? 'active' : ''}`}>
          <Link 
            to="/news" 
            className={`mobile-nav-link ${location.pathname === '/news' || location.pathname === '/' ? 'active' : ''}`}
            onClick={closeMenu}
          >
            <span className="nav-icon">🎯</span>
            뉴스 큐레이팅
          </Link>
          <Link 
            to="/dashboard"
            className={`mobile-nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}
            onClick={closeMenu}
          >
            <span className="nav-icon">📊</span>
            대시보드
          </Link>
          {isLogin ? (
            <button className="mobile-nav-button logout-btn" onClick={logout}>
              <span className="nav-icon">👋</span>
              로그아웃
            </button>
          ) : (
            <Link 
              to="/login"
              className="mobile-nav-link login-btn"
              onClick={closeMenu}
            >
              <span className="nav-icon">🔐</span>
              로그인
            </Link>
          )}
        </nav>

        {/* Mobile Overlay */}
        <div 
          className={`mobile-overlay ${isMenuOpen ? 'active' : ''}`}
          onClick={closeMenu}
        ></div>
      </div>
    </header>
  )
}

export default TheHeader