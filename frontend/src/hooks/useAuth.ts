import { useState } from 'react'
import { login, getMe } from '../api/search'
import { useAuthStore } from '../store/authStore'

export function useAuth() {
  const { setAuth, logout, token, user, isAuthenticated } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const signIn = async (username: string, password: string) => {
    setLoading(true)
    setError(null)
    try {
      const tokenResp = await login(username, password)
      // Temporarily store token so getMe can use it
      setAuth(tokenResp.access_token, { id: '', username, display_name: '', company_id: '', company_name: '', assigned_plays: [] })
      const me = await getMe()
      setAuth(tokenResp.access_token, me)
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Login failed. Please check your credentials.')
      logout()
    } finally {
      setLoading(false)
    }
  }

  const signOut = () => {
    logout()
  }

  return { signIn, signOut, loading, error, token, user, isAuthenticated: isAuthenticated() }
}
