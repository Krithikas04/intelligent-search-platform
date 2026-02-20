"""In-memory relational store loaded from CSV/JSON files."""
import csv
import json
import logging
import os
from functools import lru_cache
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

from backend.models.domain import (
    Asset,
    Feedback,
    Play,
    PlayAssignment,
    Rep,
    Submission,
    User,
)


def _csv_path(filename: str, data_dir: str) -> str:
    return os.path.join(data_dir, "database", filename)


def _load_csv(path: str) -> List[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


class DataStore:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self._users: Dict[str, User] = {}
        self._plays: Dict[str, Play] = {}
        self._reps: Dict[str, Rep] = {}
        self._assets: Dict[str, Asset] = {}
        self._submissions: Dict[str, Submission] = {}
        self._feedback: Dict[str, Feedback] = {}
        self._assignments: List[PlayAssignment] = []
        self._companies: Dict[str, dict] = {}
        self._load_all()

    def _load_all(self):
        db = self.data_dir + "/database"

        # Companies
        company_path = os.path.join(db, "BigSpring_takehome_data - comapny.json")
        with open(company_path, encoding="utf-8") as f:
            company_data = json.load(f)
        for c in company_data["companies"]:
            self._companies[c["id"]] = c

        # Users
        for row in _load_csv(os.path.join(db, "BigSpring_takehome_data - users.csv")):
            u = User(
                id=row["id"],
                username=row["username"],
                display_name=row["display_name"],
                role=row["role"],
                company_id=row["company_id"],
                is_active=row["is_active"].upper() == "TRUE",
            )
            self._users[u.id] = u

        # Plays
        for row in _load_csv(os.path.join(db, "BigSpring_takehome_data - play.csv")):
            p = Play(
                id=row["id"],
                company_id=row["company_id"],
                title=row["title"],
                description=row["description"],
                is_active=row["is_active"].upper() == "TRUE",
            )
            self._plays[p.id] = p

        # Reps
        for row in _load_csv(os.path.join(db, "BigSpring_takehome_data - rep.csv")):
            r = Rep(
                id=row["id"],
                prompt_text=row["prompt_text"],
                prompt_title=row["prompt_title"],
                prompt_type=row["prompt_type"],
                play_id=row["play_id"],
                company_id=row["company_id"],
                asset_id=row.get("asset_id") or None,
            )
            self._reps[r.id] = r

        # Assets
        for row in _load_csv(os.path.join(db, "BigSpring_takehome_data - asset.csv")):
            a = Asset(
                id=row["id"],
                type=row["type"],
                file_name=row["file_name"],
                company_id=row["company_id"],
            )
            self._assets[a.id] = a

        # Submissions
        for row in _load_csv(os.path.join(db, "BigSpring_takehome_data - submission.csv")):
            s = Submission(
                id=row["id"],
                user_id=row["user_id"],
                rep_id=row["rep_id"],
                submitted_at=row["submitted_at"],
                submission_type=row["submission_type"],
                asset_id=row["asset_id"],
                company_id=row["company_id"],
            )
            self._submissions[s.id] = s

        # Feedback
        for row in _load_csv(os.path.join(db, "BigSpring_takehome_data - feedback.csv")):
            fb = Feedback(
                id=row["id"],
                submission_id=row["submission_id"],
                company_id=row["company_id"],
                score=int(row["score"]),
                text=row["text"],
                created_at=row["created_at"],
            )
            self._feedback[fb.id] = fb

        # Play assignments
        for row in _load_csv(os.path.join(db, "BigSpring_takehome_data - play_assignment.csv")):
            pa = PlayAssignment(
                id=row["id"],
                user_id=row["user_id"],
                play_id=row["play_id"],
                assigned_date=row["assigned_date"],
                status=row["status"],
                completed_at=row.get("completed_at") or None,
            )
            self._assignments.append(pa)

        self._validate_integrity()

    def _validate_integrity(self) -> None:
        """Warn about referential integrity issues in the source data."""
        # Assignments referencing missing plays
        for asgn in self._assignments:
            if asgn.play_id not in self._plays:
                logger.warning("DATA: assignment %s → play %s not found", asgn.id, asgn.play_id)
            if asgn.user_id not in self._users:
                logger.warning("DATA: assignment %s → user %s not found", asgn.id, asgn.user_id)

        # Submissions referencing missing users, reps, or assets
        for sub in self._submissions.values():
            if sub.user_id not in self._users:
                logger.warning("DATA: submission %s → user %s not found", sub.id, sub.user_id)
            if sub.rep_id not in self._reps:
                logger.warning("DATA: submission %s → rep %s not found", sub.id, sub.rep_id)
            if sub.asset_id not in self._assets:
                logger.warning("DATA: submission %s → asset %s not found", sub.id, sub.asset_id)

        # Reps referencing missing plays
        for rep in self._reps.values():
            if rep.play_id not in self._plays:
                logger.warning("DATA: rep %s → play %s not found", rep.id, rep.play_id)

    # --- Lookup helpers ---

    def get_user_by_username(self, username: str) -> Optional[User]:
        for u in self._users.values():
            if u.username == username:
                return u
        return None

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def get_company(self, company_id: str) -> Optional[dict]:
        return self._companies.get(company_id)

    def get_play(self, play_id: str) -> Optional[Play]:
        return self._plays.get(play_id)

    def get_rep(self, rep_id: str) -> Optional[Rep]:
        return self._reps.get(rep_id)

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        return self._assets.get(asset_id)

    def get_submissions_for_user(self, user_id: str) -> List[Submission]:
        return [s for s in self._submissions.values() if s.user_id == user_id]

    def get_feedback_for_submission(self, submission_id: str) -> Optional[Feedback]:
        for fb in self._feedback.values():
            if fb.submission_id == submission_id:
                return fb
        return None

    def get_assignments_for_user(self, user_id: str) -> List[PlayAssignment]:
        return [a for a in self._assignments if a.user_id == user_id]

    def get_plays_for_company(self, company_id: str) -> List[Play]:
        return [p for p in self._plays.values() if p.company_id == company_id]

    def get_reps_for_play(self, play_id: str) -> List[Rep]:
        return [r for r in self._reps.values() if r.play_id == play_id]

    def get_assets_for_company(self, company_id: str) -> List[Asset]:
        return [a for a in self._assets.values() if a.company_id == company_id]

    def all_submissions(self) -> List[Submission]:
        return list(self._submissions.values())

    def all_assets(self) -> List[Asset]:
        return list(self._assets.values())

    def all_plays(self) -> List[Play]:
        return list(self._plays.values())

    def all_reps(self) -> List[Rep]:
        return list(self._reps.values())

    def asset_file_path(self, file_name: str) -> str:
        return os.path.join(self.data_dir, "assets", file_name)


_store: Optional[DataStore] = None


def get_data_store() -> DataStore:
    global _store
    if _store is None:
        from backend.config import get_settings
        _store = DataStore(get_settings().data_dir)
    return _store
