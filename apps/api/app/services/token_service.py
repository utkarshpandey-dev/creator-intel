"""Provides a valid YouTube access token for a channel, refreshing when expired.

Tokens are stored encrypted. This service is the only place they are decrypted, used, and
(after a refresh) re-encrypted and persisted — so callers never handle plaintext secrets.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import channels as channel_repo
from .crypto import get_cipher
from .youtube import YouTubeClient

# Refresh a little early so a token can't expire mid-import.
_EXPIRY_SKEW = timedelta(seconds=120)


class TokenError(Exception):
    pass


async def get_valid_access_token(
    session: AsyncSession, client: httpx.AsyncClient, channel_id: uuid.UUID
) -> str:
    token = await channel_repo.get_oauth_token(session, channel_id)
    if token is None:
        raise TokenError("Channel has no stored OAuth token")

    cipher = get_cipher()
    now = datetime.now(timezone.utc)

    if token.expires_at and token.expires_at - _EXPIRY_SKEW > now:
        return cipher.decrypt(token.access_token_encrypted)

    # Expired (or unknown expiry) → refresh.
    if not token.refresh_token_encrypted:
        raise TokenError("Access token expired and no refresh token is available")

    refresh_token = cipher.decrypt(token.refresh_token_encrypted)
    refreshed = await YouTubeClient(client).refresh_access_token(refresh_token)

    await channel_repo.upsert_oauth_token(
        session,
        channel_id=channel_id,
        access_token_encrypted=cipher.encrypt(refreshed.access_token),
        refresh_token_encrypted=(
            cipher.encrypt(refreshed.refresh_token) if refreshed.refresh_token else None
        ),
        scope=refreshed.scope,
        expires_at=now + timedelta(seconds=refreshed.expires_in),
    )
    return refreshed.access_token
