from pydantic import BaseModel, Field
from typing import Optional, Literal, List


class SearchRequest(BaseModel):
    query: str = Field(..., max_length=500)
    mode: Optional[Literal["auto", "knowledge", "performance"]] = "auto"


class SourceChunk(BaseModel):
    asset_id: str
    asset_type: str  # pdf | video | audio | image
    play_id: Optional[str] = None
    play_title: str
    rep_title: str
    chunk_text: str
    page_number: Optional[int] = None
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    score: Optional[float] = None
    section_id: Optional[str] = None
    heading: Optional[str] = None
    feedback_score: Optional[int] = None


class IntentResult(BaseModel):
    intent: Literal[
        "assigned_knowledge",
        "performance_history",
        "combined",
        "general_professional",
        "out_of_scope",
    ]
    confidence: float
    reasoning: str


class Recommendation(BaseModel):
    play_id: str
    play_title: str
    rep_id: Optional[str] = None
    rep_title: Optional[str] = None
    status: str
    reason: str


class SearchResponse(BaseModel):
    intent: IntentResult
    response_tier: Literal["tier1", "tier2", "tier3", "grounded"]
    answer: str
    sources: List[SourceChunk] = []
    recommendations: List[Recommendation] = []


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserMeResponse(BaseModel):
    id: str
    username: str
    display_name: str
    company_id: str
    company_name: str
    assigned_plays: List[dict]
