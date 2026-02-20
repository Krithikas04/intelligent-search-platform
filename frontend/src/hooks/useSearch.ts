import { useCallback, useRef, useState } from 'react'
import { searchStream } from '../api/search'
import type { SearchRequest, StreamMetaEvent, StreamState } from '../types'

const TIER3_ANSWER =
  "I couldn't find any specific information in your assigned training materials that " +
  "addresses this query. This may be because the topic isn't covered in your current " +
  "plays, or your query may be too specific. Try rephrasing your question or explore " +
  "the recommendations below."

const INITIAL_STATE: StreamState = {
  intent: null,
  response_tier: null,
  sources: [],
  recommendations: [],
  answer: '',
  isStreaming: false,
  isDone: false,
  error: null,
}

export function useSearch() {
  const [state, setState] = useState<StreamState>(INITIAL_STATE)
  const abortRef = useRef<AbortController | null>(null)

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setState(INITIAL_STATE)
  }, [])

  const doSearch = useCallback(async (payload: SearchRequest) => {
    // Cancel any in-flight request
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setState({ ...INITIAL_STATE, isStreaming: true })

    await searchStream(
      payload,
      (event) => {
        switch (event.type) {
          case 'meta': {
            const meta = event as StreamMetaEvent
            setState((prev) => ({
              ...prev,
              intent: meta.intent,
              response_tier: meta.response_tier,
              sources: meta.sources,
              recommendations: meta.recommendations,
            }))
            break
          }

          case 'chunk':
            setState((prev) => ({ ...prev, answer: prev.answer + event.content }))
            break

          case 'done':
            setState((prev) => {
              // If the LLM returned INSUFFICIENT_CONTEXT, replace with the tier3 message
              const isInsufficient = event.is_insufficient || prev.answer.trim() === 'INSUFFICIENT_CONTEXT'
              return {
                ...prev,
                answer: isInsufficient ? TIER3_ANSWER : prev.answer,
                response_tier: isInsufficient ? 'tier3' : prev.response_tier,
                isStreaming: false,
                isDone: true,
              }
            })
            break

          case 'error':
            setState((prev) => ({
              ...prev,
              isStreaming: false,
              isDone: true,
              error: event.message,
            }))
            break
        }
      },
      controller.signal,
    )
  }, [])

  return { doSearch, reset, state }
}
