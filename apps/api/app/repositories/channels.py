"""Repositories for channels and their content.

ChannelRepository is org-scoped (a channel belongs to an organization). Videos and comments
hang off a channel, so their upserts are scoped by channel_id — callers must first resolve
the channel through ChannelRepository, which guarantees it belongs to the caller's org.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Channel, Comment, OAuthToken, Video
from .base import TenantRepository


class ChannelRepository(TenantRepository[Channel]):
    model = Channel

    async def get_by_external_id(self, provider: str, external_id: str) -> Channel | None:
        res = await self.session.execute(
            self._scoped().where(
                Channel.provider == provider, Channel.external_id == external_id
            )
        )
        return res.scalar_one_or_none()

    async def upsert_youtube_channel(self, snippet_stats: dict) -> Channel:
        """Create or update a channel from a YouTube channels.list item."""
        existing = await self.get_by_external_id("youtube", snippet_stats["external_id"])
        target = existing or Channel(
            organization_id=self.organization_id,
            provider="youtube",
            external_id=snippet_stats["external_id"],
        )
        for field in ("title", "handle", "thumbnail_url", "subscriber_count",
                      "video_count", "view_count"):
            if field in snippet_stats:
                setattr(target, field, snippet_stats[field])
        if existing is None:
            self.session.add(target)
        await self.session.flush()
        return target


async def upsert_oauth_token(
    session: AsyncSession,
    *,
    channel_id: uuid.UUID,
    access_token_encrypted: str,
    refresh_token_encrypted: str | None,
    scope: str | None,
    expires_at: datetime | None,
) -> None:
    stmt = insert(OAuthToken).values(
        channel_id=channel_id,
        access_token_encrypted=access_token_encrypted,
        refresh_token_encrypted=refresh_token_encrypted,
        scope=scope,
        expires_at=expires_at,
    )
    update_set = {
        "access_token_encrypted": stmt.excluded.access_token_encrypted,
        "scope": stmt.excluded.scope,
        "expires_at": stmt.excluded.expires_at,
        "updated_at": datetime.now(timezone.utc),
    }
    # Only overwrite the refresh token if we actually received a new one.
    if refresh_token_encrypted is not None:
        update_set["refresh_token_encrypted"] = stmt.excluded.refresh_token_encrypted
    stmt = stmt.on_conflict_do_update(index_elements=[OAuthToken.channel_id], set_=update_set)
    await session.execute(stmt)


async def get_oauth_token(session: AsyncSession, channel_id: uuid.UUID) -> OAuthToken | None:
    res = await session.execute(
        select(OAuthToken).where(OAuthToken.channel_id == channel_id)
    )
    return res.scalar_one_or_none()


async def bulk_upsert_videos(
    session: AsyncSession, channel_id: uuid.UUID, rows: list[dict]
) -> None:
    if not rows:
        return
    for row in rows:
        stmt = insert(Video).values(channel_id=channel_id, **row)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_video",
            set_={
                "title": stmt.excluded.title,
                "description": stmt.excluded.description,
                "view_count": stmt.excluded.view_count,
                "like_count": stmt.excluded.like_count,
                "comment_count": stmt.excluded.comment_count,
                "stats": stmt.excluded.stats,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        await session.execute(stmt)


async def bulk_upsert_comments(
    session: AsyncSession, channel_id: uuid.UUID, rows: list[dict]
) -> None:
    if not rows:
        return
    for row in rows:
        stmt = insert(Comment).values(channel_id=channel_id, **row)
        # Comments are immutable once posted; ignore re-imports of the same comment.
        stmt = stmt.on_conflict_do_nothing(constraint="uq_comment")
        await session.execute(stmt)


async def video_id_map(
    session: AsyncSession, channel_id: uuid.UUID
) -> dict[str, uuid.UUID]:
    """Map provider video id -> our internal video UUID, to link comments."""
    res = await session.execute(
        select(Video.external_id, Video.id).where(Video.channel_id == channel_id)
    )
    return {external_id: vid for external_id, vid in res.all()}
