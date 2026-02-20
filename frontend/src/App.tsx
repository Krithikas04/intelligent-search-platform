import React, { useEffect } from 'react'
import { useAuthStore } from './store/authStore'
import { LoginPage } from './components/auth/LoginPage'
import { SearchPage } from './components/search/SearchPage'
import { getMe } from './api/search'

// ── Error Boundary ────────────────────────────────────────────────────────────

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50">
          <div className="text-center p-8 max-w-md">
            <h1 className="text-2xl font-bold text-red-600 mb-2">Something went wrong</h1>
            <p className="text-slate-500 text-sm mb-6 font-mono">
              {this.state.error?.message ?? 'Unknown error'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Reload page
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

// ── App ───────────────────────────────────────────────────────────────────────

function AppContent() {
  const token = useAuthStore((s) => s.token)

  // Verify the persisted token with the server on every mount.
  // If the token is invalid/tampered the 401 interceptor in client.ts will
  // clear localStorage and reload, landing the user on the login page.
  useEffect(() => {
    if (!token) return
    getMe().catch(() => {
      // 401 interceptor handles clearing storage + reload
    })
  }, [token])

  if (!token) return <LoginPage />
  return <SearchPage />
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  )
}
