import { Navigate } from 'react-router-dom'
import type { ReactNode } from 'react'

interface ProtectedRouteProps {
  children: ReactNode
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
  const token = localStorage.getItem('access_token')

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return children
}

export default ProtectedRoute