import { Routes, Route } from 'react-router-dom'
import { NewsView, NewsDetailView, DashBoardView, NotFoundView } from '../pages'
import { LoginForm, RegisterForm, ProtectedRoute } from '../features/auth'

export const AppRouter = () => {
  return (
    <Routes>
      <Route path="/" element={<NewsView />} />
      <Route path="/news" element={<NewsView />} />
      <Route path="/login" element={<LoginForm />} />
      <Route path="/register" element={<RegisterForm />} />
      <Route 
        path="/news/:id" 
        element={
          <ProtectedRoute>
            <NewsDetailView />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <DashBoardView />
          </ProtectedRoute>
        } 
      />
      <Route path="*" element={<NotFoundView />} />
    </Routes>
  )
}