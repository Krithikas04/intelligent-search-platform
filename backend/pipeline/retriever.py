"""
Scoped Pinecone retriever — security core.
build_pinecone_filter() is the single most security-critical function in the system.
company_id is ALWAYS included in every filter; it is never skippable.
"""
from typing import List

from openai import OpenAI
from pinecone import Pinecone

from backend.config import get_settings
from backend.core.user_context import UserContext
from backend.models.api_schemas import SourceChunk

settings = get_settings()


def build_pinecone_filter(user_context: UserContext, intent: str) -> dict:
    """
    Build a Pinecone metadata pre-filter for the given intent.

    INVARIANT: company_id is ALWAYS in the filter — no path through this
    function returns a filter without the company_id constraint.
    """
    # SECURITY: company_id fence — always enforced
    company_fence = {"company_id": {"$eq": user_context.company_id}}

    knowledge_filter = {
        "$and": [
            company_fence,
            {"content_type": {"$eq": "knowledge"}},
            # assignment fence — only plays the user is assigned to
            {"play_id": {"$in": user_context.assigned_play_ids}},
        ]
    }

    submission_filter = {
        "$and": [
            company_fence,
            {"content_type": {"$eq": "submission"}},
            # per-user fence — only this user's own submissions
            {"user_id": {"$eq": user_context.user_id}},
        ]
    }

    combined_filter = {
        "$and": [
            company_fence,
            {
                "$or": [
                    {
                        "$and": [
                            {"content_type": {"$eq": "knowledge"}},
                            {"play_id": {"$in": user_context.assigned_play_ids}},
                        ]
                    },
                    {
                        "$and": [
                            {"content_type": {"$eq": "submission"}},
                            {"user_id": {"$eq": user_context.user_id}},
                        ]
                    },
                ]
            },
        ]
    }

    if intent == "performance_history":
        return submission_filter
    elif intent == "combined":
        return combined_filter
    else:
        # assigned_knowledge, general_professional (also search knowledge), anything else
        return knowledge_filter


def retrieve_chunks(
    query: str,
    user_context: UserContext,
    intent: str,
) -> List[SourceChunk]:
    """Embed query, apply scoped filter, return top-k source chunks."""
    if not user_context.assigned_play_ids and intent != "performance_history":
        return []

    openai_client = OpenAI(api_key=settings.openai_api_key)
    embedding_response = openai_client.embeddings.create(
        model=settings.embedding_model,
        input=query,
        dimensions=settings.embedding_dimensions,
    )
    query_vector = embedding_response.data[0].embedding

    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index_name)

    pinecone_filter = build_pinecone_filter(user_context, intent)

    results = index.query(
        vector=query_vector,
        top_k=settings.pinecone_top_k,
        include_metadata=True,
        filter=pinecone_filter,
    )

    # Pinecone v8 returns an object with .matches; metadata is always a dict
    raw_matches = getattr(results, "matches", []) or []
    chunks = []
    for match in raw_matches:
        score = match.score if hasattr(match, "score") else match.get("score", 0.0)
        if score < settings.similarity_threshold:
            continue
        meta: dict = match.metadata if hasattr(match, "metadata") else match.get("metadata", {})
        chunks.append(
            SourceChunk(
                asset_id=meta.get("asset_id", ""),
                asset_type=meta.get("asset_type", ""),
                play_id=meta.get("play_id"),
                play_title=meta.get("play_title", ""),
                rep_title=meta.get("rep_title", ""),
                chunk_text=meta.get("chunk_text", ""),
                page_number=meta.get("page_number"),
                timestamp_start=meta.get("timestamp_start"),
                timestamp_end=meta.get("timestamp_end"),
                score=score,
                section_id=meta.get("section_id"),
                heading=meta.get("heading"),
                feedback_score=meta.get("feedback_score"),
            )
        )

    return chunks
