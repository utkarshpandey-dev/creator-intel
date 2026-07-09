"""Stage 1 — cheap spam/low-value filter. Pure code, zero LLM tokens.

Drops the bulk of comment volume (bot spam, self-promo, emoji-only, trivially short) before
anything is embedded or reasoned over. Returning a reason aids debugging and tuning.
"""

from __future__ import annotations

import re

_URL = re.compile(r"https?://|www\.", re.IGNORECASE)
_ALNUM = re.compile(r"[a-z0-9]", re.IGNORECASE)

# Common self-promo / bot patterns on YouTube.
_SPAM_PHRASES = (
    "sub for sub",
    "sub4sub",
    "check my channel",
    "check out my channel",
    "subscribe to my",
    "who is watching in",
    "free followers",
    "make money online",
    "click my profile",
)


def keep_reason(text: str, *, min_words: int) -> str | None:
    """Return a rejection reason, or None if the comment should be kept."""
    stripped = (text or "").strip()
    if not stripped:
        return "empty"
    if not _ALNUM.search(stripped):
        return "no_alphanumeric"  # emoji-only / punctuation-only
    if _URL.search(stripped):
        return "contains_link"
    lowered = stripped.lower()
    if any(phrase in lowered for phrase in _SPAM_PHRASES):
        return "spam_phrase"
    if len(stripped.split()) < min_words:
        return "too_short"
    return None


def should_keep(text: str, *, min_words: int) -> bool:
    return keep_reason(text, min_words=min_words) is None
