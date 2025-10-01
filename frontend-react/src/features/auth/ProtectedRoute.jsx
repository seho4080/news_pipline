import { Navigate } from 'react-router-dom'

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('access_token')
  
  if (!token) {
    alert("로그인이 필요한 서비스입니다.")
    return <Navigate to="/login" replace />
  }
  
  return children
}

export default ProtectedRoute