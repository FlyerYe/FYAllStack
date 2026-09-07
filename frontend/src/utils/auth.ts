export type UserRole = 'admin' | 'user'

interface JwtPayload {
  role?: unknown
}

export function getCurrentUserRole(): UserRole | null {
  const token = localStorage.getItem('access_token')
  if (!token) {
    return null
  }

  const [, payload] = token.split('.')
  if (!payload) {
    return null
  }

  try {
    const normalizedPayload = payload.replace(/-/g, '+').replace(/_/g, '/')
    const decoded = JSON.parse(atob(normalizedPayload)) as JwtPayload
    return decoded.role === 'admin' || decoded.role === 'user' ? decoded.role : null
  } catch {
    return null
  }
}
