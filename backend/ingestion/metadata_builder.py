"""Attaches Pinecone metadata to each chunk. This is the security-critical file."""
from typing import Optional


def _strip_none(d: dict) -> dict:
    """Pinecone rejects null metadata values — remove any key whose value is None."""
    return {k: v for k, v in d.items() if v is not None}


def build_knowledge_metadata(
    chunk: dict,
    *,
    company_id: str,
    asset_id: str,
    play_id: str,
    rep_id: Optional[str],
    asset_type: str,
    play_title: str,
    rep_title: str,
    company_name: str,
) -> dict:
    """Build Pinecone metadata for a knowledge content chunk."""
    return _strip_none({
        "company_id": company_id,        # SECURITY: always in filter
        "content_type": "knowledge",
        "asset_id": asset_id,
        "play_id": play_id,              # SECURITY: assignment check via $in
        "rep_id": rep_id or "",
        "asset_type": asset_type,        # pdf | video | audio | image
        "page_number": chunk.get("page_number"),
        "timestamp_start": chunk.get("timestamp_start"),
        "timestamp_end": chunk.get("timestamp_end"),
        "section_id": chunk.get("section_id") or "",
        "heading": chunk.get("heading") or "",
        "play_title": play_title,
        "rep_title": rep_title,
        "company_name": company_name,
        "chunk_text": chunk["chunk_text"][:2000],  # stored for retrieval display
        "chunk_index": chunk["chunk_index"],
    })


def build_submission_metadata(
    chunk: dict,
    *,
    company_id: str,
    asset_id: str,
    play_id: str,
    rep_id: str,
    user_id: str,
    submission_id: str,
    asset_type: str,
    play_title: str,
    rep_title: str,
    company_name: str,
) -> dict:
    """Build Pinecone metadata for a submission chunk (per-user isolation)."""
    return _strip_none({
        "company_id": company_id,         # SECURITY: always in filter
        "content_type": "submission",
        "asset_id": asset_id,
        "play_id": play_id,
        "rep_id": rep_id,
        "user_id": user_id,              # CRITICAL: per-user isolation
        "submission_id": submission_id,
        "asset_type": asset_type,
        "timestamp_start": chunk.get("timestamp_start"),
        "timestamp_end": chunk.get("timestamp_end"),
        "section_id": chunk.get("section_id") or "",
        "heading": chunk.get("heading") or "",
        "play_title": play_title,
        "rep_title": rep_title,
        "company_name": company_name,
        "chunk_text": chunk["chunk_text"][:2000],
        "chunk_index": chunk["chunk_index"],
        "feedback_score": chunk.get("feedback_score"),
        "feedback_text": (chunk.get("feedback_text") or "")[:500],
        "has_feedback": chunk.get("has_feedback", False),
    })
