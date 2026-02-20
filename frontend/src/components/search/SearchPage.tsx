import { useAuth } from '../../hooks/useAuth'
import { useSearch } from '../../hooks/useSearch'
import { SearchBar } from './SearchBar'
import { AnswerCard } from './AnswerCard'
import { RecommendationPanel } from './RecommendationPanel'

export function SearchPage() {
  const { user, signOut } = useAuth()
  const { doSearch, reset, state } = useSearch()

  const handleSearch = (query: string, mode: 'auto' | 'knowledge' | 'performance') => {
    reset()
    doSearch({ query, mode })
  }

  const hasResult = state.isDone || state.isStreaming

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Knowledge Search</p>
              {user && <p className="text-xs text-slate-500">{user.company_name}</p>}
            </div>
          </div>

          {user && (
            <div className="flex items-center gap-3">
              <div className="text-right hidden sm:block">
                <p className="text-sm text-slate-300">{user.display_name}</p>
                <p className="text-xs text-slate-500">{user.assigned_plays.length} plays assigned</p>
              </div>
              <button
                onClick={signOut}
                className="text-xs text-slate-500 hover:text-slate-300 transition-colors px-2 py-1"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Assigned plays summary — only on empty state */}
        {user && user.assigned_plays.length > 0 && !hasResult && (
          <div className="bg-slate-800/40 rounded-xl border border-slate-700/60 p-4">
            <p className="text-xs font-medium text-slate-400 mb-2">Your assigned training plays</p>
            <div className="flex flex-wrap gap-2">
              {user.assigned_plays.map((ap) => (
                <span
                  key={ap.play_id}
                  className="text-xs px-2.5 py-1 rounded-full bg-slate-700 text-slate-300 border border-slate-600"
                >
                  {ap.play_title}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Search bar */}
        <SearchBar
          onSearch={handleSearch}
          isLoading={state.isStreaming}
          intent={state.intent}
        />

        {/* Error state */}
        {state.error && (
          <div className="bg-red-900/30 border border-red-800 rounded-xl p-4 text-sm text-red-300">
            Search failed: {state.error}
          </div>
        )}

        {/* Retrieving indicator (before meta arrives) */}
        {state.isStreaming && !state.response_tier && (
          <div className="flex flex-col items-center justify-center py-16 gap-4">
            <div className="flex gap-1.5">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
            <p className="text-sm text-slate-500">Searching your training materials…</p>
          </div>
        )}

        {/* Answer + recommendations */}
        {state.response_tier && (
          <div className="space-y-6">
            <AnswerCard
              intent={state.intent!}
              response_tier={state.response_tier}
              answer={state.answer}
              sources={state.sources}
              recommendations={state.recommendations}
              isStreaming={state.isStreaming}
            />
            {state.isDone && state.recommendations.length > 0 && (
              <RecommendationPanel recommendations={state.recommendations} />
            )}
          </div>
        )}

        {/* Empty state */}
        {!hasResult && !state.error && (
          <div className="text-center py-20 space-y-3">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-800 border border-slate-700">
              <svg className="w-7 h-7 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-slate-400 text-sm">Ask a question about your training materials</p>
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              {[
                'What are the key benefits of Amproxin?',
                'How does GridMaster optimize server racks?',
                'Show me my recent pitch feedback',
                'How do I handle pricing objections?',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => handleSearch(suggestion, 'auto')}
                  className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-400 hover:text-slate-300 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
