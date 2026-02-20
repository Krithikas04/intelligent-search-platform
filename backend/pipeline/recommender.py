"""Rule-based Play/Rep recommendation — no LLM call."""
from typing import List, Optional, Set

from backend.core.data_store import DataStore
from backend.core.user_context import UserContext
from backend.models.api_schemas import Recommendation

# Status priority: in_progress > assigned > completed
STATUS_PRIORITY = {"in-progress": 0, "in_progress": 0, "assigned": 1, "completed": 2}


def _status_rank(status: str) -> int:
    return STATUS_PRIORITY.get(status.lower(), 3)


def _query_relevance_score(query: str, play_title: str) -> int:
    """
    Returns count of query words found in the play title (case-insensitive).
    Higher = more relevant to the query.
    """
    query_words = set(query.lower().split())
    title_words = set(play_title.lower().split())
    return len(query_words & title_words)


def get_recommendations(
    user_context: UserContext,
    retrieved_play_ids: Set[str],
    store: DataStore,
    max_recs: int = 3,
    query: Optional[str] = None,
) -> List[Recommendation]:
    """
    Recommend assigned plays/reps that were NOT already retrieved.
    Rank by: query relevance first, then in_progress > assigned > completed.
    """
    candidates = []
    for ap in user_context.assigned_plays:
        if ap.play_id in retrieved_play_ids:
            continue
        candidates.append(ap)

    # Sort: most query-relevant first; break ties by status priority
    if query:
        candidates.sort(
            key=lambda ap: (
                -_query_relevance_score(query, ap.play_title),
                _status_rank(ap.status),
            )
        )
    else:
        candidates.sort(key=lambda ap: _status_rank(ap.status))

    recommendations = []
    for ap in candidates[:max_recs]:
        # Find next incomplete rep in this play
        reps = store.get_reps_for_play(ap.play_id)
        next_rep = None
        for rep in reps:
            if rep.prompt_type == "watch":
                next_rep = rep
                break
        if next_rep is None and reps:
            next_rep = reps[0]

        # Build reason text — mention query relevance when applicable
        relevance = _query_relevance_score(query or "", ap.play_title)
        if relevance > 0:
            reason = f"'{ap.play_title}' covers content related to your query."
        elif ap.status in ("in_progress", "in-progress"):
            reason = f"You are currently working through '{ap.play_title}'. Continue where you left off."
        elif ap.status == "assigned":
            reason = f"'{ap.play_title}' has been assigned to you and is ready to start."
        else:
            reason = f"You've completed '{ap.play_title}'. Review it to reinforce your knowledge."

        recommendations.append(
            Recommendation(
                play_id=ap.play_id,
                play_title=ap.play_title,
                rep_id=next_rep.id if next_rep else None,
                rep_title=next_rep.prompt_title if next_rep else None,
                status=ap.status,
                reason=reason,
            )
        )

    return recommendations
