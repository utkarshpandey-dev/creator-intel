"""Encryption for OAuth tokens at rest.

OAuth refresh tokens are long-lived credentials to a creator's channel — a breach of the
tokens table must not expose them. We encrypt with Fernet (AES-128-CBC + HMAC) using an
app-managed key.

Production hardening path: replace the single app key with a KMS-wrapped data key
(envelope encryption). The interface below stays the same, so only this file changes.
"""

from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from ..config import get_settings


class TokenCipher:
    def __init__(self, key: str) -> None:
        if not key:
            raise RuntimeError(
                "TOKEN_ENCRYPTION_KEY is not set. Generate one with "
                "`python -c \"from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())\"`"
            )
        self._fernet = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as exc:  # tampered or wrong key
            raise RuntimeError("Failed to decrypt token (invalid key or corrupted data)") from exc


@lru_cache
def get_cipher() -> TokenCipher:
    return TokenCipher(get_settings().token_encryption_key)
