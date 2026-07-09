"""Signed OAuth `state` parameter.

The Google callback arrives without our Clerk session (it's a top-level redirect from
Google), so we cannot read the caller's identity from a JWT there. Instead we mint a
short-lived signed token *at connect-start* that carries the org/user context, and verify
its signature at the callback. This both (a) restores tenant context and (b) prevents CSRF
— an attacker cannot forge a valid state.
"""

from __future__ import annotations

import secrets
import time

import jwt

from ..config import get_settings

_ALGO = "HS256"


def issue_state(*, organization_id: str, user_id: str) -> str:
    settings = get_settings()
    now = int(time.time())
    payload = {
        "org": organization_id,
        "sub": user_id,
        "nonce": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + settings.oauth_state_ttl,
    }
    return jwt.encode(payload, settings.internal_api_secret, algorithm=_ALGO)


def verify_state(state: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(state, settings.internal_api_secret, algorithms=[_ALGO])
    except jwt.PyJWTError as exc:
        raise ValueError(f"Invalid OAuth state: {exc}") from exc
