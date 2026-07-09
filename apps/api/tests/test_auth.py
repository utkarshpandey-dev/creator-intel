"""Auth verification rejects malformed tokens before any network call."""

import pytest

from app.auth import AuthError, verify_token


def test_malformed_token_rejected():
    with pytest.raises(AuthError):
        verify_token("this-is-not-a-jwt")
