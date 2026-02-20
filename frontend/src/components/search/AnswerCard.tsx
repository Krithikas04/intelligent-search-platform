import ReactMarkdown from 'react-markdown'
import type { ResponseTier, IntentResult, SourceChunk, Recommendation } from '../../types'
import { CitationList } from './CitationList'

const TIER_CONFIG: Record<ResponseTier, {
  label: string
  border: string
  badge: string
  dot: string
}> = {
  grounded: {
    label: 'Grounded Answer',
    border: 'border-green-700',
    badge: 'bg-green-900/60 text-green-300 border-green-700',
    dot: 'bg-green-400',
  },
  tier2: {
    label: 'General Knowledge',
    border: 'border-amber-700',
    badge: 'bg-amber-900/60 text-amber-300 border-amber-700',
    dot: 'bg-amber-400',
  },
  tier3: {
    label: 'No Results Found',
    border: 'border-slate-600',
    badge: 'bg-slate-800 text-slate-400 border-slate-600',
    dot: 'bg-slate-500',
  },
  tier1: {
    label: 'Out of Scope',
    border: 'border-red-800',
    badge: 'bg-red-900/60 text-red-400 border-red-800',
    dot: 'bg-red-500',
  },
}

interface Props {
  intent: IntentResult
  response_tier: ResponseTier
  answer: string
  sources: SourceChunk[]
  recommendations: Recommendation[]
  isStreaming: boolean
}

export function AnswerCard({ intent: _intent, response_tier, answer, sources, isStreaming }: Props) {
  const config = TIER_CONFIG[response_tier]

  return (
    <div data-testid="answer-card" className={`bg-slate-800/80 rounded-xl border ${config.border} overflow-hidden`}>
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-700/60">
        <span className={`w-2 h-2 rounded-full ${config.dot} flex-shrink-0 ${isStreaming ? 'animate-pulse' : ''}`} />
        <span className={`text-xs px-2 py-0.5 rounded border font-medium ${config.badge}`}>
          {config.label}
        </span>
        {isStreaming && (
          <span className="text-xs text-slate-500 animate-pulse">Generating…</span>
        )}
        {!isStreaming && sources.length > 0 && (
          <span className="text-xs text-slate-500 ml-auto">
            {sources.length} source{sources.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Answer body */}
      <div className="px-4 py-4">
        <div className="prose prose-sm prose-invert max-w-none text-slate-200 leading-relaxed">
          <ReactMarkdown>{answer}</ReactMarkdown>
          {/* Blinking cursor while streaming */}
          {isStreaming && (
            <span className="inline-block w-0.5 h-4 bg-indigo-400 ml-0.5 align-middle animate-pulse" />
          )}
        </div>
      </div>

      {/* Citations */}
      {sources.length > 0 && (
        <div className="px-4 pb-4">
          <CitationList sources={sources} />
        </div>
      )}
    </div>
  )
}
