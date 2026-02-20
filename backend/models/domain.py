from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class User(BaseModel):
    id: str
    username: str
    display_name: str
    role: str
    company_id: str
    is_active: bool


class Play(BaseModel):
    id: str
    company_id: str
    title: str
    description: str
    is_active: bool


class Rep(BaseModel):
    id: str
    prompt_text: str
    prompt_title: str
    prompt_type: str
    play_id: str
    company_id: str
    asset_id: Optional[str] = None


class Asset(BaseModel):
    id: str
    type: str  # pdf | video | audio | image | text
    file_name: str
    company_id: str


class Submission(BaseModel):
    id: str
    user_id: str
    rep_id: str
    submitted_at: str
    submission_type: str
    asset_id: str
    company_id: str


class Feedback(BaseModel):
    id: str
    submission_id: str
    company_id: str
    score: int
    text: str
    created_at: str


class PlayAssignment(BaseModel):
    id: str
    user_id: str
    play_id: str
    assigned_date: str
    status: str
    completed_at: Optional[str] = None
