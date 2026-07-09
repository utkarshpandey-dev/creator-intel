"""Connected creator channels and their (encrypted) OAuth credentials."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, Timestamps, UUIDPrimaryKey


class Channel(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "channels"
    __table_args__ = (
        UniqueConstraint("organization_id", "provider", "external_id", name="uq_channel"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String, default="youtube")
    external_id: Mapped[str] = mapped_column(String, index=True)  # provider channel id
    title: Mapped[str | None] = mapped_column(String)
    handle: Mapped[str | None] = mapped_column(String)
    thumbnail_url: Mapped[str | None] = mapped_column(String)
    subscriber_count: Mapped[int | None] = mapped_column(BigInteger)
    video_count: Mapped[int | None] = mapped_column(BigInteger)
    view_count: Mapped[int | None] = mapped_column(BigInteger)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    oauth_token: Mapped["OAuthToken | None"] = relationship(
        back_populates="channel", cascade="all, delete-orphan", uselist=False
    )


class OAuthToken(UUIDPrimaryKey, Timestamps, Base):
    """Encrypted at rest. Only the Milestone 4 token service decrypts these."""

    __tablename__ = "oauth_tokens"

    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), unique=True, index=True
    )
    access_token_encrypted: Mapped[str] = mapped_column(String)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(String)
    scope: Mapped[str | None] = mapped_column(String)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    channel: Mapped["Channel"] = relationship(back_populates="oauth_token")
