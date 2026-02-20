import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.config import get_settings, Settings
from backend.core.data_store import DataStore, get_data_store
from backend.core.rate_limiter import limiter
from backend.core.security import create_access_token
from backend.core.user_context import build_user_context
from backend.models.api_schemas import TokenRequest, TokenResponse, UserMeResponse
from backend.dependencies import get_current_user
from backend.core.user_context import UserContext

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/token", response_model=TokenResponse)
@limiter.limit("30/minute")
def login(
    request: Request,
    body: TokenRequest,
    store: DataStore = Depends(get_data_store),
    settings: Settings = Depends(get_settings),
):
    user = store.get_user_by_username(body.username)
    if user is None or not user.is_active:
        logger.warning("Failed login attempt for username=%r", body.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if body.password != settings.demo_password:
        logger.warning("Failed login attempt for username=%r (wrong password)", body.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(user.id, user.company_id)
    logger.info("User %s (%s) logged in", user.id, user.username)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserMeResponse)
def get_me(
    ctx: UserContext = Depends(get_current_user),
    store: DataStore = Depends(get_data_store),
):
    company = store.get_company(ctx.company_id)
    return UserMeResponse(
        id=ctx.user_id,
        username=ctx.username,
        display_name=ctx.display_name,
        company_id=ctx.company_id,
        company_name=company["name"] if company else ctx.company_id,
        assigned_plays=[
            {
                "play_id": ap.play_id,
                "play_title": ap.play_title,
                "status": ap.status,
                "completed_at": ap.completed_at,
            }
            for ap in ctx.assigned_plays
        ],
    )
