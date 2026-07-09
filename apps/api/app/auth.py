"""Clerk session-token (JWT) verification.

Clerk issues short-lived RS256 JWTs. We verify them against Clerk's published JWKS
(cached, keys rotate rarely) and derive the caller's identity from standard claims.
The backend never trusts a client-supplied user or org id — only what a valid,
unexpired, correctly-issued token asserts.
"""

from __future__ import annotations

from dataclasses import dataclass

import jwt
from jwt import PyJWKClient

from .config import get_settings

# PyJWKClient caches keys in-process and refreshes on unknown-kid, so we build it once.
_jwk_client: PyJWKClient | None = None


def _client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(get_settings().jwks_url)
    return _jwk_client


@dataclass(frozen=True)
class Identity:
    """The authenticated caller, derived purely from a verified token."""

    user_id: str  # Clerk user id (claim: sub)
    org_id: str | None  # active organization id (claim: org_id), if any
    org_role: str | None  # role within the active org (claim: org_role)


class AuthError(Exception):
    """Raised when a token is missing, malformed, expired, or untrusted."""


def verify_token(token: str) -> Identity:
    settings = get_settings()
    try:
        signing_key = _client().get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            options={"require": ["exp", "iat", "sub"]},
            leeway=5,  # small clock-skew tolerance
        )
    except jwt.PyJWTError as exc:
        raise AuthError(str(exc)) from exc

    # Defense-in-depth: if authorized parties are configured, enforce them.
    azp = claims.get("azp")
    if settings.clerk_authorized_parties and azp not in settings.clerk_authorized_parties:
        raise AuthError("Untrusted authorized party")

    return Identity(
        user_id=claims["sub"],
        org_id=claims.get("org_id"),
        org_role=claims.get("org_role"),
    )
