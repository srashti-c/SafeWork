import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { clearToken, getMe, getToken, login } from './api'

// Holds "who is logged in" for the whole app.
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(getToken()))

  // On page load: if a token is stored, ask the server who we are.
  useEffect(() => {
    if (!getToken()) return
    getMe()
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setLoading(false))
  }, [])

  // api.js sends this event when the server answers 401 (token expired or invalid).
  useEffect(() => {
    const onUnauthorized = () => setUser(null)
    window.addEventListener('safework-unauthorized', onUnauthorized)
    return () => window.removeEventListener('safework-unauthorized', onUnauthorized)
  }, [])

  const signIn = useCallback(async (email, password) => {
    await login(email, password)
    const me = await getMe()
    setUser(me)
    return me
  }, [])

  const signOut = useCallback(() => {
    clearToken()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}