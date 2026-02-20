import type { Recommendation } from '../../types'

const STATUS_CONFIG = {
  in_progress: { label: 'In Progress', color: 'text-blue-400', dot: 'bg-blue-400' },
  'in-progress': { label: 'In Progress', color: 'text-blue-400', dot: 'bg-blue-400' },
  assigned: { label: 'Assigned', color: 'text-yellow-400', dot: 'bg-yellow-400' },
  completed: { label: 'Completed', color: 'text-green-400', dot: 'bg-green-400' },
}

function getStatusConfig(status: string) {
  return STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] ?? {
    label: status,
    color: 'text-slate-400',
    dot: 'bg-slate-400',
  }
}

interface Props {
  recommendations: Recommendation[]
}

export function RecommendationPanel({ recommendations }: Props) {
  if (recommendations.length === 0) return null

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <h3 className="text-sm font-medium text-slate-300">Recommended Next Steps</h3>
      </div>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {recommendations.map((rec) => {
          const sc = getStatusConfig(rec.status)
          return (
            <div
              key={rec.play_id}
              className="bg-slate-800/60 rounded-lg border border-slate-700 p-3 space-y-2 hover:border-slate-600 transition-colors"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium text-white leading-snug">{rec.play_title}</p>
                <div className={`flex items-center gap-1.5 flex-shrink-0 ${sc.color}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${sc.dot}`} />
                  <span className="text-xs">{sc.label}</span>
                </div>
              </div>

              {rec.rep_title && (
                <p className="text-xs text-slate-400">
                  <span className="text-slate-600">Next: </span>
                  {rec.rep_title}
                </p>
              )}

              <p className="text-xs text-slate-500 leading-relaxed">{rec.reason}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
