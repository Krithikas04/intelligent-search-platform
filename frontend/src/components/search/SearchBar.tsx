import { useState, FormEvent } from 'react'
import type { IntentResult } from '../../types'

const INTENT_LABELS: Record<string, string> = {
  assigned_knowledge: 'Knowledge',
  performance_history: 'Performance',
  combined: 'Combined',
  general_professional: 'General',
  out_of_scope: 'Out of Scope',
}

const INTENT_COLORS: Record<string, string> = {
  assigned_knowledge: 'bg-blue-900/50 text-blue-300 border-blue-700',
  performance_history: 'bg-purple-900/50 text-purple-300 border-purple-700',
  combined: 'bg-cyan-900/50 text-cyan-300 border-cyan-700',
  general_professional: 'bg-amber-900/50 text-amber-300 border-amber-700',
  out_of_scope: 'bg-red-900/50 text-red-300 border-red-700',
}

interface Props {
  onSearch: (query: string, mode: 'auto' | 'knowledge' | 'performance') => void
  isLoading: boolean
  intent?: IntentResult | null
}

export function SearchBar({ onSearch, isLoading, intent }: Props) {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<'auto' | 'knowledge' | 'performance'>('auto')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    onSearch(query.trim(), mode)
  }

  return (
    <div className="w-full space-y-2">
      <form onSubmit={handleSubmit} className="relative flex gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value.slice(0, 500))}
            placeholder="Ask anything about your training materials or performance..."
            className="w-full pl-4 pr-24 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-500">
            {query.length}/500
          </span>
        </div>

        <select
          value={mode}
          onChange={(e) => setMode(e.target.value as typeof mode)}
          className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-xl text-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent cursor-pointer"
        >
          <option value="auto">Auto</option>
          <option value="knowledge">Knowledge</option>
          <option value="performance">Performance</option>
        </select>

        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:cursor-not-allowed text-white font-medium rounded-xl text-sm transition-colors flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Searching
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Search
            </>
          )}
        </button>
      </form>

      {intent && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Detected intent:</span>
          <span
            className={`text-xs px-2.5 py-0.5 rounded-full border font-medium ${INTENT_COLORS[intent.intent]}`}
          >
            {INTENT_LABELS[intent.intent]}
          </span>
          <span className="text-xs text-slate-600">
            {(intent.confidence * 100).toFixed(0)}% confidence
          </span>
        </div>
      )}
    </div>
  )
}
