import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8003'

export const apiClient = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor: attach JWT from localStorage
apiClient.interceptors.request.use((config) => {
  const raw = localStorage.getItem('auth-store')
  if (raw) {
    try {
      const parsed = JSON.parse(raw)
      const token = parsed?.state?.token
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    } catch {
      // ignore parse errors
    }
  }
  return config
})

// Response interceptor: 401 on protected routes → clear token and reload.
// IMPORTANT: skip /auth/token so login failures propagate as errors instead of causing a reload.
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const isAuthEndpoint = err.config?.url?.includes('/auth/token')
    if (err.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('auth-store')
      window.location.reload()
    }
    return Promise.reject(err)
  }
)
