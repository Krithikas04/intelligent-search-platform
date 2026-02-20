import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from backend.core.rate_limiter import limiter
from backend.dependencies import get_current_user
from backend.core.user_context import UserContext
from backend.models.api_schemas import SearchRequest, SearchResponse
from backend.pipeline.orchestrator import Orchestrator

router = APIRouter(tags=["search"])
logger = logging.getLogger(__name__)

_orchestrator: Orchestrator | None = None


def _get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


@router.post("/search", response_model=SearchResponse)
@limiter.limit("60/minute")
async def search(
    request: Request,
    body: SearchRequest,
    ctx: UserContext = Depends(get_current_user),
    orchestrator: Orchestrator = Depends(_get_orchestrator),
) -> SearchResponse:
    """Non-streaming search — returns the full response in one JSON payload."""
    logger.info("Search: user=%s query=%r mode=%s", ctx.user_id, body.query[:80], body.mode)
    return await orchestrator.run(query=body.query, mode=body.mode, user_context=ctx)


@router.post("/search/stream")
@limiter.limit("60/minute")
async def search_stream(
    request: Request,
    body: SearchRequest,
    ctx: UserContext = Depends(get_current_user),
    orchestrator: Orchestrator = Depends(_get_orchestrator),
) -> StreamingResponse:
    """
    Streaming search — returns SSE events.

    Event sequence:
      data: {"type": "meta",  "intent": {...}, "response_tier": "...", "sources": [...], "recommendations": [...]}
      data: {"type": "chunk", "content": "<token>"}   ← repeated
      data: {"type": "done",  "is_insufficient": false}
      data: {"type": "error", "message": "..."}       ← only on failure
    """
    logger.info("Stream search: user=%s query=%r mode=%s", ctx.user_id, body.query[:80], body.mode)

    async def event_generator():
        async for event in orchestrator.run_stream(
            query=body.query, mode=body.mode, user_context=ctx
        ):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",          # disable nginx buffering
            "Connection": "keep-alive",
        },
    )
