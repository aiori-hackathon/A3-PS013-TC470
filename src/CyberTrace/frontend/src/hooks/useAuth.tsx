import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, setToken, ApiError } from '../api/client'
import type { TokenResponse, User } from '../types/auth'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const hasToken = Boolean(localStorage.getItem('cybertrace_token'))
    if (!hasToken) {
      setIsLoading(false)
      return
    }
    api
      .get<User>('/api/auth/me')
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setIsLoading(false))
  }, [])

  async function login(email: string, password: string) {
    setError(null)
    try {
      const tokenResp = await api.post<TokenResponse>('/api/auth/login', { email, password })
      setToken(tokenResp.access_token)
      const me = await api.get<User>('/api/auth/me')
      setUser(me)
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Unable to reach the server'
      setError(message)
      throw err
    }
  }

  function logout() {
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
