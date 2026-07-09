"""Stage 4 — cluster comment embeddings into themes. Pure ML, zero LLM tokens.

Turns thousands of unique comments into ~dozens of themes. The reasoning model (M6) then
sees only cluster summaries, so cost scales with theme count, not comment count.
"""

from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize


def choose_k(n_items: int, max_clusters: int) -> int:
    """Heuristic cluster count: enough themes to be useful, capped for cost/readability."""
    if n_items <= 2:
        return 1
    # ~ one cluster per 15 comments, bounded by [2, max_clusters] and n_items.
    return max(2, min(max_clusters, n_items // 15 or 2, n_items))


def cluster_vectors(vectors: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (labels, centroids). Vectors are L2-normalized so KMeans ~ cosine k-means."""
    unit = normalize(vectors)
    model = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = model.fit_predict(unit)
    return labels, model.cluster_centers_
