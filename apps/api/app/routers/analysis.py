"""Endpoints exposing the comment-pipeline output (themes) and triggering re-processing."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime

from ..db.session import get_db
from ..deps import current_org, current_plan_limits
from ..models import Channel, CommentCluster, Insight, Organization, Report, Video
from ..services.billing import PlanLimits
from ..repositories.channels import ChannelRepository
from ..services.queue import enqueue_comment_pipeline, enqueue_report

router = APIRouter(prefix="/channels", tags=["analysis"])


class ThemeOut(BaseModel):
    id: uuid.UUID
    label: str | None
    summary: str | None
    size: int
    sentiment: float | None
    theme_kind: str | None


async def _owned_channel(
    channel_id: uuid.UUID, org: Organization, db: AsyncSession
) -> Channel:
    channel = await ChannelRepository(db, org.id).get(channel_id)
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel


@router.post("/{channel_id}/process", status_code=status.HTTP_202_ACCEPTED)
async def process_channel(
    channel_id: uuid.UUID,
    org: Organization = Depends(current_org),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await _owned_channel(channel_id, org, db)
    await enqueue_comment_pipeline(org.id, channel_id)
    return {"status": "queued"}


@router.get("/{channel_id}/themes", response_model=list[ThemeOut])
async def list_themes(
    channel_id: uuid.UUID,
    kind: str | None = Query(default=None, description="filter: request/complaint/praise/other"),
    limit: int = Query(default=50, le=200),
    org: Organization = Depends(current_org),
    db: AsyncSession = Depends(get_db),
) -> list[ThemeOut]:
    await _owned_channel(channel_id, org, db)
    stmt = (
        select(CommentCluster)
        .where(CommentCluster.channel_id == channel_id)
        .order_by(CommentCluster.size.desc())
        .limit(limit)
    )
    if kind:
        stmt = stmt.where(CommentCluster.theme_kind == kind)
    clusters = (await db.execute(stmt)).scalars().all()
    return [ThemeOut.model_validate(c, from_attributes=True) for c in clusters]


class InsightOut(BaseModel):
    id: uuid.UUID
    kind: str
    payload: dict
    created_at: datetime


class ReportOut(BaseModel):
    id: uuid.UUID
    kind: str
    title: str | None
    content_md: str | None
    payload: dict | None
    created_at: datetime


@router.get("/{channel_id}/insights", response_model=InsightOut | None)
async def latest_insight(
    channel_id: uuid.UUID,
    org: Organization = Depends(current_org),
    db: AsyncSession = Depends(get_db),
) -> Insight | None:
    await _owned_channel(channel_id, org, db)
    return (
        await db.execute(
            select(Insight)
            .where(Insight.channel_id == channel_id)
            .order_by(Insight.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


@router.get("/{channel_id}/reports", response_model=list[ReportOut])
async def list_reports(
    channel_id: uuid.UUID,
    org: Organization = Depends(current_org),
    db: AsyncSession = Depends(get_db),
) -> list[Report]:
    await _owned_channel(channel_id, org, db)
    rows = (
        await db.execute(
            select(Report)
            .where(Report.channel_id == channel_id)
            .order_by(Report.created_at.desc())
            .limit(20)
        )
    ).scalars().all()
    return list(rows)


class VideoOut(BaseModel):
    id: uuid.UUID
    title: str | None
    view_count: int | None
    like_count: int | None
    comment_count: int | None
    published_at: datetime | None
    thumbnail_url: str | None


@router.get("/{channel_id}/videos", response_model=list[VideoOut])
async def list_videos(
    channel_id: uuid.UUID,
    limit: int = Query(default=100, le=200),
    org: Organization = Depends(current_org),
    db: AsyncSession = Depends(get_db),
) -> list[Video]:
    await _owned_channel(channel_id, org, db)
    rows = (
        await db.execute(
            select(Video)
            .where(Video.channel_id == channel_id)
            .order_by(Video.published_at.desc().nullslast())
            .limit(limit)
        )
    ).scalars().all()
    return list(rows)


@router.post("/{channel_id}/reports", status_code=status.HTTP_202_ACCEPTED)
async def request_report(
    channel_id: uuid.UUID,
    kind: str = Query(default="weekly", description="weekly or monthly"),
    org: Organization = Depends(current_org),
    limits: PlanLimits = Depends(current_plan_limits),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await _owned_channel(channel_id, org, db)
    # The monthly report runs the flagship (most expensive) model — gate it by plan so cost
    # tracks revenue. Weekly reports use cheaper tiers and stay available to all plans.
    if kind == "monthly" and not limits.monthly_report:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Monthly strategy reports require an upgrade from {limits.label}.",
        )
    await enqueue_report(org.id, channel_id, kind)
    return {"status": "queued", "kind": kind}
