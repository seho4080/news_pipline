import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import './Login.scss'

const Login = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const navigate = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/members/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username,
          password,
        })
      })

      if (!response.ok) {
        setErrorMessage("로그인 실패: " + response.status)
        return
      }

      const data = await response.json()
      
      const accessToken = data.access
      const refreshToken = data.refresh

      // 1. localStorage에 토큰 저장
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)

      // 2. axios 기본 Authorization 설정
      axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
      
      alert("로그인 성공!")

      // 3. 페이지 이동
      navigate('/', { replace: true })
    } catch (error) {
      const message = '아이디 또는 비밀번호가 올바르지 않습니다.'
      setErrorMessage(message)
      alert(message)
    }
  }

  const register = () => {
    navigate('/register', { replace: true })
  }

  return (
    <div className="login-container">
      <form onSubmit={handleLogin}>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="ID"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="PASSWORD"
          required
        />
        <button type="submit">로그인</button>
        {errorMessage && <p className="error">{errorMessage}</p>}
      </form>
      <div className="register-container">
        <p>아직 회원이 아니신가요? <button onClick={register}>회원 가입</button></p>
      </div>
    </div>
  )
}

export default Login