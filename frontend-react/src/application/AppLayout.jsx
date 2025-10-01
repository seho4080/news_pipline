import { useLocation } from 'react-router-dom'
import { TheHeader, TheFooter } from '../widgets/navigation'
import { AppRouter } from './AppRouter'

export const AppLayout = () => {
  const location = useLocation()
  const hideHeaderFooter = location.pathname === '/login' || location.pathname === '/register'

  return (
    <>
      {!hideHeaderFooter && <TheHeader />}
      <main>
        <AppRouter />
      </main>
      {!hideHeaderFooter && <TheFooter />}
    </>
  )
}