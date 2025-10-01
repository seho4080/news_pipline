import { RouterProvider } from './providers/RouterProvider'

export const AppProviders = ({ children }) => {
  return (
    <RouterProvider>
      {children}
    </RouterProvider>
  )
}