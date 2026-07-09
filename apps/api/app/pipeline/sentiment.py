"""Lightweight lexicon sentiment. Pure code, zero LLM tokens.

A cheap directional signal (-1..1) for ranking clusters and flagging complaints. Not a
substitute for the reasoning model's nuanced read — just enough to sort and route.
"""

from __future__ import annotations

import re

_POSITIVE = {
    "love", "loved", "great", "awesome", "amazing", "best", "helpful", "thanks",
    "thank", "excellent", "perfect", "good", "nice", "brilliant", "wonderful",
    "fantastic", "clear", "underrated", "goat", "fire", "please", "more",
}
_NEGATIVE = {
    "hate", "worst", "bad", "boring", "terrible", "awful", "confusing", "wrong",
    "disappointed", "disappointing", "waste", "poor", "annoying", "clickbait",
    "misleading", "stop", "unclear", "trash", "cringe", "outdated",
}
_NEGATORS = {"not", "no", "never", "dont", "don't", "isn't", "isnt", "wasn't"}
_WORD = re.compile(r"[a-z']+")


def score(text: str) -> float:
    tokens = _WORD.findall((text or "").lower())
    pos = neg = 0
    for i, tok in enumerate(tokens):
        negated = i > 0 and tokens[i - 1] in _NEGATORS
        if tok in _POSITIVE:
            neg += 1 if negated else 0
            pos += 0 if negated else 1
        elif tok in _NEGATIVE:
            pos += 1 if negated else 0
            neg += 0 if negated else 1
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 4)
