"""
Master orchestrator: classify → retrieve → generate → recommend.

Three-Tier Response Policy:
  Tier 1 (out_of_scope)         → Polite refusal, no retrieval
  Tier 2 (general_professional) → LLM general answer, no retrieval
  Tier 3 (no retrieval results) → "Couldn't find information" message
  Grounded (retrieved chunks)   → Cited answer from context

Streaming SSE event sequence:
  {"type": "meta",  "intent": {...}, "response_tier": "...", "sources": [...], "recommendations": [...]}
  {"type": "chunk", "content": "<text token>"}   ← repeated
  {"type": "done",  "is_insufficient": false}
  {"type": "error", "message": "..."}            ← only on failure
"""
import asyncio
import json
from typing import AsyncIterator, Optional

from backend.core.data_store import get_data_store
from backend.core.user_context import UserContext
from backend.models.api_schemas import IntentResult, SearchResponse, SourceChunk
from backend.pipeline.intent_classifier import classify_intent
from backend.pipeline.retriever import retrieve_chunks
from backend.pipeline.generator import (
    generate_grounded_answer,
    generate_general_answer,
    stream_grounded_answer,
    stream_general_answer,
)
from backend.pipeline.recommender import get_recommendations

OUT_OF_SCOPE_ANSWER = (
    "I am a specialized search engine for your assigned BigSpring materials. "
    "I cannot assist with queries outside of your professional scope."
)

TIER3_ANSWER = (
    "I couldn't find any specific information in your assigned training materials that "
    "addresses this query. This may be because the topic isn't covered in your current "
    "plays, or your query may be too specific. Try rephrasing your question or explore "
    "the recommendations below."
)


def _sse(data: dict) -> str:
    """Format a dict as a single SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


def _apply_mode(intent_result: IntentResult, mode: Optional[str]) -> None:
    """Override LLM-classified intent based on explicit user mode selection (in-place)."""
    if mode == "knowledge":
        intent_result.intent = "assigned_knowledge"
    elif mode == "performance":
        intent_result.intent = "performance_history"


def _play_id_set_from_chunks(chunks) -> set:
    """Extract play IDs directly from chunk metadata — O(n), no string matching."""
    return {c.play_id for c in chunks if c.play_id}


class Orchestrator:
    def __init__(self):
        self._store = get_data_store()

    # ── Non-streaming (/search) ───────────────────────────────────────────────

    async def run(
        self,
        query: str,
        mode: Optional[str],
        user_context: UserContext,
    ) -> SearchResponse:
        intent_result: IntentResult = classify_intent(query)
        _apply_mode(intent_result, mode)

        if intent_result.intent == "out_of_scope":
            return SearchResponse(
                intent=intent_result,
                response_tier="tier1",
                answer=OUT_OF_SCOPE_ANSWER,
                sources=[],
                recommendations=[],
            )

        if intent_result.intent == "general_professional":
            answer = generate_general_answer(query)
            recommendations = get_recommendations(user_context, set(), self._store, query=query)
            return SearchResponse(
                intent=intent_result,
                response_tier="tier2",
                answer=answer,
                sources=[],
                recommendations=recommendations,
            )

        chunks = retrieve_chunks(query, user_context, intent_result.intent)

        if not chunks:
            recommendations = get_recommendations(user_context, set(), self._store, query=query)
            return SearchResponse(
                intent=intent_result,
                response_tier="tier3",
                answer=TIER3_ANSWER,
                sources=[],
                recommendations=recommendations,
            )

        answer, is_sufficient = generate_grounded_answer(query, chunks)

        if not is_sufficient:
            recommendations = get_recommendations(user_context, set(), self._store, query=query)
            return SearchResponse(
                intent=intent_result,
                response_tier="tier3",
                answer=TIER3_ANSWER,
                sources=[],
                recommendations=recommendations,
            )

        play_id_set = _play_id_set_from_chunks(chunks)
        recommendations = get_recommendations(user_context, play_id_set, self._store, query=query)

        return SearchResponse(
            intent=intent_result,
            response_tier="grounded",
            answer=answer,
            sources=chunks,
            recommendations=recommendations,
        )

    # ── Streaming (/search/stream) ────────────────────────────────────────────

    async def run_stream(
        self,
        query: str,
        mode: Optional[str],
        user_context: UserContext,
    ) -> AsyncIterator[str]:
        """
        Async generator that yields SSE-formatted strings.

        Event sequence:
          1. meta   — intent, tier, sources, recommendations (sent before streaming)
          2. chunk  — one per LLM token
          3. done   — signals end; carries is_insufficient flag
        """
        try:
            # ── 1. Intent classification (sync → thread pool) ─────────────────
            intent_result: IntentResult = await asyncio.to_thread(classify_intent, query)
            _apply_mode(intent_result, mode)

            # ── 2. Tier 1: out of scope ───────────────────────────────────────
            if intent_result.intent == "out_of_scope":
                yield _sse({
                    "type": "meta",
                    "intent": intent_result.model_dump(),
                    "response_tier": "tier1",
                    "sources": [],
                    "recommendations": [],
                })
                yield _sse({"type": "chunk", "content": OUT_OF_SCOPE_ANSWER})
                yield _sse({"type": "done", "is_insufficient": False})
                return

            # ── 3. Tier 2: general professional ──────────────────────────────
            if intent_result.intent == "general_professional":
                recommendations = get_recommendations(user_context, set(), self._store, query=query)
                yield _sse({
                    "type": "meta",
                    "intent": intent_result.model_dump(),
                    "response_tier": "tier2",
                    "sources": [],
                    "recommendations": [r.model_dump() for r in recommendations],
                })
                async for token in stream_general_answer(query):
                    yield _sse({"type": "chunk", "content": token})
                yield _sse({"type": "done", "is_insufficient": False})
                return

            # ── 4. Retrieval (sync → thread pool) ────────────────────────────
            chunks = await asyncio.to_thread(
                retrieve_chunks, query, user_context, intent_result.intent
            )

            # ── 5. Tier 3: no results ─────────────────────────────────────────
            if not chunks:
                recommendations = get_recommendations(user_context, set(), self._store, query=query)
                yield _sse({
                    "type": "meta",
                    "intent": intent_result.model_dump(),
                    "response_tier": "tier3",
                    "sources": [],
                    "recommendations": [r.model_dump() for r in recommendations],
                })
                yield _sse({"type": "chunk", "content": TIER3_ANSWER})
                yield _sse({"type": "done", "is_insufficient": False})
                return

            # ── 6. Grounded streaming ─────────────────────────────────────────
            play_id_set = _play_id_set_from_chunks(chunks)
            recommendations = get_recommendations(user_context, play_id_set, self._store, query=query)

            # Send meta immediately so the UI can render sources while answer streams
            yield _sse({
                "type": "meta",
                "intent": intent_result.model_dump(),
                "response_tier": "grounded",
                "sources": [c.model_dump() for c in chunks],
                "recommendations": [r.model_dump() for r in recommendations],
            })

            # Buffer all tokens first to detect INSUFFICIENT_CONTEXT before sending.
            # This is a rare edge case so the buffering overhead is acceptable.
            token_buffer: list[str] = []
            async for token in stream_grounded_answer(query, chunks):
                token_buffer.append(token)

            accumulated = "".join(token_buffer)
            is_insufficient = accumulated.strip() == "INSUFFICIENT_CONTEXT"

            if is_insufficient:
                # Don't leak the sentinel — send the human-readable tier3 message
                yield _sse({"type": "chunk", "content": TIER3_ANSWER})
            else:
                for token in token_buffer:
                    yield _sse({"type": "chunk", "content": token})

            yield _sse({"type": "done", "is_insufficient": is_insufficient})

        except Exception as exc:
            yield _sse({"type": "error", "message": str(exc)})
