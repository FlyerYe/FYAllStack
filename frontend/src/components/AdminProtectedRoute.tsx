import { Navigate } from 'react-router-dom'
import type { ReactNode } from 'react'

import { getCurrentUserRole } from '../utils/auth'

interface AdminProtectedRouteProps {
  children: ReactNode
}

function AdminProtectedRoute({ children }: AdminProtectedRouteProps) {
  if (getCurrentUserRole() !== 'admin') {
    return <Navigate to="/recipes" replace />
  }

  return children
}

export default AdminProtectedRoute
