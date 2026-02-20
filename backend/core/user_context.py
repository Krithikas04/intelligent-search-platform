"""Builds a UserContext from the server-side DataStore — never from client input."""
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from backend.core.data_store import DataStore
from backend.models.domain import Play, PlayAssignment

logger = logging.getLogger(__name__)


@dataclass
class AssignedPlay:
    play_id: str
    play_title: str
    status: str
    completed_at: Optional[str]


@dataclass
class UserContext:
    user_id: str
    username: str
    display_name: str
    company_id: str
    company_name: str
    assigned_plays: List[AssignedPlay] = field(default_factory=list)

    @property
    def assigned_play_ids(self) -> List[str]:
        return [ap.play_id for ap in self.assigned_plays]


def build_user_context(user_id: str, company_id: str, store: DataStore) -> UserContext:
    user = store.get_user(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    company = store.get_company(company_id)
    company_name = company["name"] if company else company_id

    assignments: List[PlayAssignment] = store.get_assignments_for_user(user_id)
    assigned_plays: List[AssignedPlay] = []
    for asgn in assignments:
        play = store.get_play(asgn.play_id)
        if play is None:
            logger.warning(
                "Assignment %s references non-existent play %s for user %s — skipping",
                asgn.id, asgn.play_id, user_id,
            )
            continue
        assigned_plays.append(
            AssignedPlay(
                play_id=asgn.play_id,
                play_title=play.title,
                status=asgn.status,
                completed_at=asgn.completed_at,
            )
        )

    return UserContext(
        user_id=user_id,
        username=user.username,
        display_name=user.display_name,
        company_id=company_id,
        company_name=company_name,
        assigned_plays=assigned_plays,
    )
