"""AI-layer persistence: the embedding cache, structured insights, reports, and memory.

These tables are what make cost flat and advice compounding:
  - Embedding is a cache keyed by content_hash, so we never pay to embed the same text twice.
  - Insight/Report store versioned model output (model + prompt_version) for auditability.
  - MemoryRecord is the episodic, embedded creator memory retrieved via RAG.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from ..config import get_settings
from ..db.base import Base, Timestamps, UUIDPrimaryKey

_EMBED_DIM = get_settings().embedding_dim


class Embedding(UUIDPrimaryKey, Timestamps, Base):
    """Content-addressed embedding cache. Unique per (channel, content_hash)."""

    __tablename__ = "embeddings"
    __table_args__ = (
        UniqueConstraint("channel_id", "content_hash", name="uq_embedding_cache"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), index=True
    )
    content_hash: Mapped[str] = mapped_column(String, index=True)
    model: Mapped[str | None] = mapped_column(String)  # which embedding model produced it
    vector: Mapped[list[float]] = mapped_column(Vector(_EMBED_DIM))


class Insight(UUIDPrimaryKey, Timestamps, Base):
    """Structured AI output (scores, themes, requests, complaints…) for a period."""

    __tablename__ = "insights"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String, index=True)  # health/growth/sentiment/topics…
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict] = mapped_column(JSONB)
    model: Mapped[str | None] = mapped_column(String)
    prompt_version: Mapped[str | None] = mapped_column(String)


class Report(UUIDPrimaryKey, Timestamps, Base):
    """A generated weekly/monthly strategy report (human-readable markdown + payload)."""

    __tablename__ = "reports"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String, index=True)  # weekly / monthly
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    title: Mapped[str | None] = mapped_column(String)
    content_md: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSONB)
    model: Mapped[str | None] = mapped_column(String)


class MemoryRecord(UUIDPrimaryKey, Timestamps, Base):
    """Episodic, embedded creator memory. Retrieved via vector search during reasoning."""

    __tablename__ = "memory_records"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String, index=True)  # recommendation/observation/goal…
    summary: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSONB)
    vector: Mapped[list[float] | None] = mapped_column(Vector(_EMBED_DIM))
