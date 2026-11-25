import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth.jsx'

// Wraps a page: not logged in -> go to login. Wrong role -> a message.
// This is only for comfort. The server checks the role on every request.
export default function Protected({ roles, children }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <p className="p-6 text-slate-600">Loading...</p>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (roles && !roles.includes(user.role)) {
    return <p className="p-6 text-slate-700">Your role cannot open this page.</p>
  }
  return children
}