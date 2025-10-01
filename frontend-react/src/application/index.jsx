import { AppProviders } from './AppProviders'
import { AppLayout } from './AppLayout'
import './styles/global.scss'
import './styles/App.scss'

export const App = () => {
  return (
    <AppProviders>
      <AppLayout />
    </AppProviders>
  )
}

export default App