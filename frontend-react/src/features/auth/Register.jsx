import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Register.scss'

const Register = () => {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const navigate = useNavigate()

  const handleRegister = async (e) => {
    e.preventDefault()
    
    try {
      const response = await fetch("http://127.0.0.1:8000/api/members/signup/", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          email,
          password,
        }),
      })
      
      if (response.status === 201) {
        alert("회원 가입 성공 !")
        navigate("/login", { replace: true })
      } else {
        alert("회원 가입 실패 !")
        setErrorMessage("회원 가입에 실패했습니다.")
      }
    } catch (error) {
      console.log("error 발생, " + error)
      setErrorMessage("네트워크 오류가 발생했습니다.")
    }
  }

  return (
    <div className="register-container">
      <form onSubmit={handleRegister}>
        <input 
          type="text" 
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="name" 
          required
        />
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="e-mail"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="password"
          required
        />
        <button type="submit">회원가입</button>
        {errorMessage && <p className="error">{errorMessage}</p>}
      </form>
    </div>
  )
}

export default Register