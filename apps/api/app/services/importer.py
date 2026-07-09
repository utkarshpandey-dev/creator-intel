"""Imports a connected channel's stats, videos, and comments into the database.

This is the ingestion half of the pipeline (Milestone 5 adds spam-filter/dedupe/cluster on
top of the raw comments this stores). It is quota-aware via the import_* limits in settings
and is safe to re-run — all writes are upserts.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..repositories import channels as channel_repo
from ..repositories.channels import ChannelRepository
from .token_service import get_valid_access_token
from .youtube import YouTubeClient, parse_iso8601_duration


def _to_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _content_hash(text: str) -> str:
    # Normalized hash powers dedupe (Milestone 5) and the embedding cache (Milestone 6).
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()


def _author_hash(channel_id_value: str | None) -> str | None:
    # PII minimization: store a stable pseudonymous id, never the raw author identity.
    if not channel_id_value:
        return None
    return hashlib.sha256(channel_id_value.encode()).hexdigest()[:32]


def _map_video(item: dict) -> dict:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    content = item.get("contentDetails", {})
    return {
        "external_id": item["id"],
        "title": snippet.get("title"),
        "description": snippet.get("description"),
        "published_at": _parse_dt(snippet.get("publishedAt")),
        "duration_seconds": parse_iso8601_duration(content.get("duration")),
        "view_count": _to_int(stats.get("viewCount")),
        "like_count": _to_int(stats.get("likeCount")),
        "comment_count": _to_int(stats.get("commentCount")),
        "thumbnail_url": (snippet.get("thumbnails", {}).get("medium", {}) or {}).get("url"),
        "stats": stats or None,
    }


def _map_comment(thread: dict, video_uuid: uuid.UUID | None) -> dict | None:
    top = (thread.get("snippet", {}) or {}).get("topLevelComment", {})
    s = top.get("snippet", {})
    text = s.get("textDisplay") or s.get("textOriginal")
    if not text:
        return None
    author_channel = (s.get("authorChannelId", {}) or {}).get("value")
    return {
        "external_id": top.get("id") or thread.get("id"),
        "video_id": video_uuid,
        "text": text,
        "content_hash": _content_hash(text),
        "author_hash": _author_hash(author_channel),
        "published_at": _parse_dt(s.get("publishedAt")),
        # Filtering, weighting, sentiment, and clustering are applied in Milestone 5.
        "kept": True,
        "weight": 1,
    }


async def run_channel_import(
    session: AsyncSession,
    client: httpx.AsyncClient,
    *,
    organization_id: uuid.UUID,
    channel_id: uuid.UUID,
) -> dict:
    settings = get_settings()
    repo = ChannelRepository(session, organization_id)
    channel = await repo.get(channel_id)
    if channel is None:
        raise ValueError("Channel not found for organization")

    access_token = await get_valid_access_token(session, client, channel_id)
    yt = YouTubeClient(client)

    # 1. Refresh channel stats and locate the uploads playlist.
    remote = await yt.get_my_channel(access_token)
    if remote is None:
        raise ValueError("Could not fetch channel from YouTube")
    stats = remote.get("statistics", {})
    channel.subscriber_count = _to_int(stats.get("subscriberCount"))
    channel.video_count = _to_int(stats.get("videoCount"))
    channel.view_count = _to_int(stats.get("viewCount"))
    uploads_playlist = (
        remote.get("contentDetails", {})
        .get("relatedPlaylists", {})
        .get("uploads")
    )

    # 2. Import videos.
    video_ids = (
        await yt.list_upload_video_ids(access_token, uploads_playlist, settings.import_max_videos)
        if uploads_playlist
        else []
    )
    videos = await yt.get_videos(access_token, video_ids) if video_ids else []
    await channel_repo.bulk_upsert_videos(session, channel_id, [_map_video(v) for v in videos])
    await session.flush()

    # 3. Import comments, linked to their internal video ids.
    id_map = await channel_repo.video_id_map(session, channel_id)
    comment_count = 0
    for v in videos:
        video_uuid = id_map.get(v["id"])
        threads = await yt.list_video_comments(
            access_token, v["id"], settings.import_max_comments_per_video
        )
        rows = [r for t in threads if (r := _map_comment(t, video_uuid))]
        await channel_repo.bulk_upsert_comments(session, channel_id, rows)
        comment_count += len(rows)

    channel.last_synced_at = datetime.now(timezone.utc)
    await session.flush()

    return {
        "channel_id": str(channel_id),
        "videos": len(videos),
        "comments": comment_count,
    }
