"""YouTube connect flow and channel management endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db.session import get_db
from ..deps import current_org, current_plan_limits
from ..models import Organization
from ..services.billing import PlanLimits
from ..repositories import channels as channel_repo
from ..repositories.channels import ChannelRepository
from ..services import oauth_state
from ..services.crypto import get_cipher
from ..services.queue import enqueue_channel_import
from ..services.youtube import YouTubeClient, build_authorize_url

router = APIRouter(prefix="/youtube", tags=["youtube"])
settings = get_settings()


class AuthorizeOut(BaseModel):
    authorize_url: str


class ChannelOut(BaseModel):
    id: uuid.UUID
    title: str | None
    handle: str | None
    thumbnail_url: str | None
    subscriber_count: int | None
    video_count: int | None
    last_synced_at: datetime | None


@router.get("/oauth/start", response_model=AuthorizeOut)
async def oauth_start(
    org: Organization = Depends(current_org),
    limits: PlanLimits = Depends(current_plan_limits),
    db: AsyncSession = Depends(get_db),
) -> AuthorizeOut:
    """Begin the connect flow. State carries our internal org UUID across the redirect.

    Enforce the plan's channel cap *before* sending the user to Google, so the limit is a
    real entitlement gate and not a cosmetic UI hint.
    """
    existing = len(await ChannelRepository(db, org.id).list())
    if existing >= limits.max_channels:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Your {limits.label} plan allows {limits.max_channels} channel(s). "
                "Upgrade to connect more."
            ),
        )
    state = oauth_state.issue_state(
        organization_id=str(org.id), user_id=org.clerk_org_id
    )
    return AuthorizeOut(authorize_url=build_authorize_url(state))


@router.get("/oauth/callback")
async def oauth_callback(
    state: str = Query(...),
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Google redirects here. No Clerk session is present; trust is re-established via state."""
    dashboard = f"{settings.web_app_url}/dashboard"

    if error:
        return RedirectResponse(f"{dashboard}?connected=0&error={error}")

    try:
        claims = oauth_state.verify_state(state)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")

    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code")

    organization_id = uuid.UUID(claims["org"])
    cipher = get_cipher()

    async with httpx.AsyncClient(timeout=30.0) as client:
        yt = YouTubeClient(client)
        tokens = await yt.exchange_code(code)
        remote = await yt.get_my_channel(tokens.access_token)

    if remote is None:
        return RedirectResponse(f"{dashboard}?connected=0&error=no_channel")

    snippet = remote.get("snippet", {})
    stats = remote.get("statistics", {})
    thumb = (snippet.get("thumbnails", {}).get("default", {}) or {}).get("url")

    repo = ChannelRepository(db, organization_id)
    channel = await repo.upsert_youtube_channel(
        {
            "external_id": remote["id"],
            "title": snippet.get("title"),
            "handle": snippet.get("customUrl"),
            "thumbnail_url": thumb,
            "subscriber_count": _to_int(stats.get("subscriberCount")),
            "video_count": _to_int(stats.get("videoCount")),
            "view_count": _to_int(stats.get("viewCount")),
        }
    )

    await channel_repo.upsert_oauth_token(
        db,
        channel_id=channel.id,
        access_token_encrypted=cipher.encrypt(tokens.access_token),
        refresh_token_encrypted=(
            cipher.encrypt(tokens.refresh_token) if tokens.refresh_token else None
        ),
        scope=tokens.scope,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=tokens.expires_in),
    )
    await db.commit()

    # Kick off the (slow) import in the background; the user lands on the dashboard now.
    await enqueue_channel_import(organization_id, channel.id)
    return RedirectResponse(f"{dashboard}?connected=1")


@router.get("/channels", response_model=list[ChannelOut])
async def list_channels(
    org: Organization = Depends(current_org), db: AsyncSession = Depends(get_db)
) -> list[ChannelOut]:
    repo = ChannelRepository(db, org.id)
    channels = await repo.list()
    return [ChannelOut.model_validate(c, from_attributes=True) for c in channels]


@router.post("/channels/{channel_id}/sync", status_code=status.HTTP_202_ACCEPTED)
async def resync_channel(
    channel_id: uuid.UUID,
    org: Organization = Depends(current_org),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    repo = ChannelRepository(db, org.id)
    channel = await repo.get(channel_id)  # org-scoped → 404 if not this tenant's
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    await enqueue_channel_import(org.id, channel_id)
    return {"status": "queued"}


def _to_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
