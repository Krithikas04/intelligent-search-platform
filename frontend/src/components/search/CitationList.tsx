import { useState } from 'react'
import type { SourceChunk as SourceChunkType } from '../../types'
import { SourceChunk } from './SourceChunk'

interface Props {
  sources: SourceChunkType[]
}

export function CitationList({ sources }: Props) {
  const [expanded, setExpanded] = useState(false)

  if (sources.length === 0) return null

  return (
    <div className="space-y-2">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
      >
        <svg
          className={`w-4 h-4 transition-transform ${expanded ? 'rotate-90' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        {expanded ? 'Hide' : 'View'} {sources.length} source{sources.length !== 1 ? 's' : ''}
      </button>

      {expanded && (
        <div className="space-y-2 pl-1">
          {sources.map((chunk, i) => (
            <SourceChunk key={`${chunk.asset_id}-${i}`} chunk={chunk} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}
