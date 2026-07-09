"""Stage 5 — pick per-cluster exemplars and classify the theme. Pure code, zero LLM tokens.

The exemplars + label are the compact payload the reasoning model consumes instead of raw
comments. This is where "cost bounded by themes, not comments" becomes concrete.
"""

from __future__ import annotations

import numpy as np

_REQUEST_MARKERS = (
    "please", "can you", "could you", "make a", "do a", "tutorial", "part 2",
    "next video", "how to", "how do", "i wish", "i want", "request", "cover",
    "explain", "would love",
)


def classify_theme(text: str, sentiment: float) -> str:
    """Coarse theme bucket used to route audience requests vs. complaints vs. praise."""
    lowered = (text or "").lower()
    if any(m in lowered for m in _REQUEST_MARKERS):
        return "request"
    if sentiment <= -0.2:
        return "complaint"
    if sentiment >= 0.3:
        return "praise"
    return "other"


def nearest_exemplars(
    vectors: np.ndarray, centroid: np.ndarray, texts: list[str], n: int = 3
) -> list[str]:
    """Return the n texts whose vectors are closest to the cluster centroid."""
    if len(texts) == 0:
        return []
    # Cosine similarity to centroid (vectors assumed L2-normalized upstream).
    sims = vectors @ centroid
    order = np.argsort(-sims)[:n]
    return [texts[i] for i in order]
