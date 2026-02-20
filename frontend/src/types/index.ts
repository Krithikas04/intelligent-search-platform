export interface SourceChunk {
  asset_id: string
  asset_type: string
  play_title: string
  rep_title: string
  chunk_text: string
  page_number?: number | null
  timestamp_start?: string | null
  timestamp_end?: string | null
  score?: number | null
  section_id?: string | null
  heading?: string | null
  feedback_score?: number | null
}

export interface IntentResult {
  intent:
    | 'assigned_knowledge'
    | 'performance_history'
    | 'combined'
    | 'general_professional'
    | 'out_of_scope'
  confidence: number
  reasoning: string
}

export interface Recommendation {
  play_id: string
  play_title: string
  rep_id?: string | null
  rep_title?: string | null
  status: string
  reason: string
}

export interface SearchResponse {
  intent: IntentResult
  response_tier: 'tier1' | 'tier2' | 'tier3' | 'grounded'
  answer: string
  sources: SourceChunk[]
  recommendations: Recommendation[]
}

// ── Streaming SSE event types ─────────────────────────────────────────────────

export type ResponseTier = 'tier1' | 'tier2' | 'tier3' | 'grounded'

export interface StreamMetaEvent {
  type: 'meta'
  intent: IntentResult
  response_tier: ResponseTier
  sources: SourceChunk[]
  recommendations: Recommendation[]
}

export interface StreamChunkEvent {
  type: 'chunk'
  content: string
}

export interface StreamDoneEvent {
  type: 'done'
  is_insufficient: boolean
}

export interface StreamErrorEvent {
  type: 'error'
  message: string
}

export type StreamEvent =
  | StreamMetaEvent
  | StreamChunkEvent
  | StreamDoneEvent
  | StreamErrorEvent

/** Client-side state produced by useSearch while streaming. */
export interface StreamState {
  intent: IntentResult | null
  response_tier: ResponseTier | null
  sources: SourceChunk[]
  recommendations: Recommendation[]
  answer: string          // accumulated token text
  isStreaming: boolean
  isDone: boolean
  error: string | null
}

export interface SearchRequest {
  query: string
  mode?: 'auto' | 'knowledge' | 'performance'
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface AssignedPlay {
  play_id: string
  play_title: string
  status: string
  completed_at?: string | null
}

export interface UserMe {
  id: string
  username: string
  display_name: string
  company_id: string
  company_name: string
  assigned_plays: AssignedPlay[]
}
