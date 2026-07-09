"""Unit tests for the M4 building blocks that don't need Google or a DB."""

import os

import pytest
from cryptography.fernet import Fernet

# Provide deterministic secrets before importing app settings-backed modules.
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("INTERNAL_API_SECRET", "test-internal-secret")

from app.services.crypto import TokenCipher  # noqa: E402
from app.services import oauth_state  # noqa: E402
from app.services.youtube import parse_iso8601_duration  # noqa: E402


def test_token_cipher_roundtrip():
    cipher = TokenCipher(Fernet.generate_key().decode())
    secret = "ya29.super-secret-refresh-token"
    encrypted = cipher.encrypt(secret)
    assert encrypted != secret
    assert cipher.decrypt(encrypted) == secret


def test_token_cipher_requires_key():
    with pytest.raises(RuntimeError):
        TokenCipher("")


def test_oauth_state_roundtrip():
    state = oauth_state.issue_state(organization_id="org-uuid", user_id="user_123")
    claims = oauth_state.verify_state(state)
    assert claims["org"] == "org-uuid"
    assert claims["sub"] == "user_123"
    assert "nonce" in claims


def test_oauth_state_rejects_tampering():
    with pytest.raises(ValueError):
        oauth_state.verify_state("not.a.valid.token")


@pytest.mark.parametrize(
    "iso,seconds",
    [
        ("PT1M30S", 90),
        ("PT1H", 3600),
        ("PT2H15M10S", 8110),
        ("P1DT2H", 93600),
        (None, None),
        ("garbage", None),
    ],
)
def test_parse_iso8601_duration(iso, seconds):
    assert parse_iso8601_duration(iso) == seconds
