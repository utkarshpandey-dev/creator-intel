"""Ingested content: videos, comments, and the theme clusters comments roll up into."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from ..config import get_settings
from ..db.base import Base, Timestamps, UUIDPrimaryKey

_EMBED_DIM = get_settings().embedding_dim


class Video(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "videos"
    __table_args__ = (UniqueConstraint("channel_id", "external_id", name="uq_video"),)

    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str] = mapped_column(String, index=True)  # provider video id
    title: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    view_count: Mapped[int | None] = mapped_column(BigInteger)
    like_count: Mapped[int | None] = mapped_column(BigInteger)
    comment_count: Mapped[int | None] = mapped_column(BigInteger)
    thumbnail_url: Mapped[str | None] = mapped_column(String)
    # Point-in-time stats snapshot, enables historical/self-comparison analysis.
    stats: Mapped[dict | None] = mapped_column(JSONB)


class CommentCluster(UUIDPrimaryKey, Timestamps, Base):
    """A semantic theme discovered by the pipeline (Milestone 5). No LLM required to form."""

    __tablename__ = "comment_clusters"

    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str | None] = mapped_column(String)
    summary: Mapped[str | None] = mapped_column(Text)
    size: Mapped[int] = mapped_column(Integer, default=0)  # weighted comment count
    sentiment: Mapped[float | None] = mapped_column(Float)
    theme_kind: Mapped[str | None] = mapped_column(String)  # request/complaint/praise/other
    centroid: Mapped[list[float] | None] = mapped_column(Vector(_EMBED_DIM))


class Comment(UUIDPrimaryKey, Timestamps, Base):
    """Raw -> filtered -> weighted. content_hash powers dedupe and the embedding cache."""

    __tablename__ = "comments"
    __table_args__ = (
        UniqueConstraint("channel_id", "external_id", name="uq_comment"),
        Index("ix_comment_channel_hash", "channel_id", "content_hash"),
    )

    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), index=True
    )
    video_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), index=True
    )
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("comment_clusters.id", ondelete="SET NULL"), index=True
    )
    external_id: Mapped[str] = mapped_column(String, index=True)  # provider comment id
    author_hash: Mapped[str | None] = mapped_column(String)  # PII-minimized identity
    text: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String, index=True)
    weight: Mapped[int] = mapped_column(Integer, default=1)  # near-duplicate collapse count
    kept: Mapped[bool] = mapped_column(default=True)  # False once spam-filtered
    sentiment: Mapped[float | None] = mapped_column(Float)
    language: Mapped[str | None] = mapped_column(String)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
