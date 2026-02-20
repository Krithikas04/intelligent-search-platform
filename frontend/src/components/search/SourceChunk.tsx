import type { SourceChunk as SourceChunkType } from '../../types'

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 8 ? 'bg-green-900/60 text-green-300 border-green-700' :
    score >= 6 ? 'bg-yellow-900/60 text-yellow-300 border-yellow-700' :
    score >= 4 ? 'bg-orange-900/60 text-orange-300 border-orange-700' :
    'bg-red-900/60 text-red-300 border-red-700'
  return (
    <span className={`text-xs px-2 py-0.5 rounded border font-medium ${color}`}>
      Score {score}/10
    </span>
  )
}

interface Props {
  chunk: SourceChunkType
  index: number
}

export function SourceChunk({ chunk, index }: Props) {
  return (
    <div className="bg-slate-800/60 rounded-lg border border-slate-700 p-3 space-y-2">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-mono text-slate-500">#{index + 1}</span>
          <span className="text-xs font-medium text-slate-300">{chunk.play_title}</span>
          <span className="text-slate-600">·</span>
          <span className="text-xs text-slate-400">{chunk.rep_title}</span>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {/* Type badge */}
          <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 uppercase tracking-wide">
            {chunk.asset_type}
          </span>
          {/* Citation badge */}
          {chunk.page_number != null && (
            <span className="text-xs px-2 py-0.5 rounded bg-blue-900/50 text-blue-300 border border-blue-800">
              Page {chunk.page_number}
            </span>
          )}
          {chunk.timestamp_start && (
            <span className="text-xs px-2 py-0.5 rounded bg-indigo-900/50 text-indigo-300 border border-indigo-800">
              {chunk.timestamp_start}–{chunk.timestamp_end}
            </span>
          )}
          {chunk.feedback_score != null && (
            <ScoreBadge score={chunk.feedback_score} />
          )}
        </div>
      </div>
      <p className="text-xs text-slate-400 leading-relaxed line-clamp-4">{chunk.chunk_text}</p>
      {chunk.score != null && (
        <p className="text-xs text-slate-600">Relevance: {(chunk.score * 100).toFixed(1)}%</p>
      )}
    </div>
  )
}
