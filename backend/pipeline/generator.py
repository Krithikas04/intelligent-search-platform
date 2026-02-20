"""Grounded response generator with inline citations — provider decided by model name."""
from typing import AsyncIterator, List, Tuple

from langchain_core.messages import HumanMessage, SystemMessage

from backend.config import get_settings
from backend.core.llm_factory import get_llm
from backend.models.api_schemas import SourceChunk

settings = get_settings()

GROUNDED_SYSTEM_PROMPT = """You are a knowledgeable sales training assistant for an enterprise learning platform.

Your task is to answer the user's query using ONLY the context chunks provided below.

Rules:
1. Answer ONLY from the provided context. Do not use outside knowledge.
2. Add inline citations after each claim in this format:
   - For PDF content: [Source: {play_title} — {rep_title}, Page {page_number}]
   - For video/audio: [Source: {play_title} — {rep_title}, {timestamp_start}–{timestamp_end}]
   - For images: [Source: {play_title} — {rep_title}, Image]
   - For submissions: [Your submission — {rep_title}, Score: {feedback_score}/10]
3. If the context is insufficient to answer the question, respond with exactly: INSUFFICIENT_CONTEXT
4. Be concise and professional. Structure your answer clearly.
5. Do not fabricate information not present in the context."""

GENERAL_PROFESSIONAL_PROMPT = """You are a professional sales training coach.

Answer the following question using your general professional knowledge about sales, communication,
and business skills.

Add a disclaimer at the end: "This response is based on general professional knowledge and does not come from your assigned learning content."

Be concise and practical."""


def _build_context_block(chunks: List[SourceChunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        citation_hint = ""
        if chunk.page_number:
            citation_hint = f"[Page {chunk.page_number}]"
        elif chunk.timestamp_start:
            citation_hint = f"[{chunk.timestamp_start}–{chunk.timestamp_end}]"
        elif chunk.feedback_score is not None:
            citation_hint = f"[Score: {chunk.feedback_score}/10]"

        parts.append(
            f"--- Chunk {i} ---\n"
            f"Play: {chunk.play_title}\n"
            f"Rep: {chunk.rep_title}\n"
            f"Type: {chunk.asset_type} {citation_hint}\n"
            f"Content: {chunk.chunk_text}\n"
        )
    return "\n".join(parts)


# ── Non-streaming (used by /search) ──────────────────────────────────────────

def generate_grounded_answer(query: str, chunks: List[SourceChunk]) -> Tuple[str, bool]:
    """Returns (answer_text, is_sufficient)."""
    llm = get_llm(settings.model, max_tokens=1024, temperature=0.1)
    context_block = _build_context_block(chunks)
    messages = [
        SystemMessage(content=GROUNDED_SYSTEM_PROMPT),
        HumanMessage(content=f"Context chunks:\n{context_block}\n\nUser query: {query}"),
    ]
    response = llm.invoke(messages)
    answer = response.content.strip()
    if answer == "INSUFFICIENT_CONTEXT":
        return answer, False
    return answer, True


def generate_general_answer(query: str) -> str:
    """General professional answer — no grounding."""
    llm = get_llm(settings.model, max_tokens=512, temperature=0.3)
    messages = [
        SystemMessage(content=GENERAL_PROFESSIONAL_PROMPT),
        HumanMessage(content=query),
    ]
    return llm.invoke(messages).content.strip()


# ── Streaming (used by /search/stream) ───────────────────────────────────────

async def stream_grounded_answer(
    query: str, chunks: List[SourceChunk]
) -> AsyncIterator[str]:
    """Yield answer text tokens from the grounded LLM call."""
    llm = get_llm(settings.model, max_tokens=1024, temperature=0.1)
    context_block = _build_context_block(chunks)
    messages = [
        SystemMessage(content=GROUNDED_SYSTEM_PROMPT),
        HumanMessage(content=f"Context chunks:\n{context_block}\n\nUser query: {query}"),
    ]
    async for chunk in llm.astream(messages):
        text = chunk.content
        if text:
            yield str(text)


async def stream_general_answer(query: str) -> AsyncIterator[str]:
    """Yield general professional answer tokens."""
    llm = get_llm(settings.model, max_tokens=512, temperature=0.3)
    messages = [
        SystemMessage(content=GENERAL_PROFESSIONAL_PROMPT),
        HumanMessage(content=query),
    ]
    async for chunk in llm.astream(messages):
        text = chunk.content
        if text:
            yield str(text)
