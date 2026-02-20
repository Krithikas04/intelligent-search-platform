import { apiClient } from './client'
import type { SearchRequest, SearchResponse, StreamEvent, TokenResponse, UserMe } from '../types'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8003'

function getToken(): string | null {
  try {
    const raw = localStorage.getItem('auth-store')
    return raw ? JSON.parse(raw)?.state?.token ?? null : null
  } catch {
    return null
  }
}

export async function login(username: string, password: string): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>('/auth/token', { username, password })
  return res.data
}

export async function getMe(): Promise<UserMe> {
  const res = await apiClient.get<UserMe>('/auth/me')
  return res.data
}

export async function search(payload: SearchRequest): Promise<SearchResponse> {
  const res = await apiClient.post<SearchResponse>('/search', payload)
  return res.data
}

/**
 * Streaming search via SSE.
 * Uses fetch + ReadableStream so POST is supported (EventSource is GET-only).
 *
 * Calls the appropriate callback for each SSE event type:
 *   onEvent(event) — receives parsed StreamEvent objects
 */
export async function searchStream(
  payload: SearchRequest,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const token = getToken()

  const response = await fetch(`${baseURL}/search/stream`, {
    method: 'POST',
    signal,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem('auth-store')
      window.location.reload()
    }
    onEvent({ type: 'error', message: `HTTP ${response.status}` })
    return
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // SSE lines are separated by \n; double \n separates events
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''   // keep the last incomplete line in buffer

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const data = line.slice(6).trim()
      if (!data) continue
      try {
        onEvent(JSON.parse(data) as StreamEvent)
      } catch {
        // ignore malformed events
      }
    }
  }
}
