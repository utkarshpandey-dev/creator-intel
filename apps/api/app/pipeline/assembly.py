"""Pure cluster assembly: vectors + metadata -> theme clusters.

Extracted from the DB orchestrator so the numeric core (normalize, cluster, weight, pick
exemplars, classify) is unit-testable without a database or embedding API.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from sklearn.preprocessing import normalize

from .clustering import choose_k, cluster_vectors
from .representatives import classify_theme, nearest_exemplars


@dataclass
class ClusterResult:
    member_indices: list[int]
    label: str | None
    summary: str
    size: int  # sum of member weights
    sentiment: float
    theme_kind: str
    centroid: list[float]


def assemble_clusters(
    texts: list[str],
    weights: list[int],
    sentiments: list[float],
    vectors: np.ndarray,
    *,
    max_clusters: int,
    min_comments_to_cluster: int,
) -> list[ClusterResult]:
    n = len(texts)
    if n == 0:
        return []

    unit = normalize(vectors)
    if n < min_comments_to_cluster:
        labels = np.zeros(n, dtype=int)
        centroids = unit.mean(axis=0, keepdims=True)
    else:
        k = choose_k(n, max_clusters)
        labels, centroids = cluster_vectors(vectors, k)

    by_label: dict[int, list[int]] = defaultdict(list)
    for idx, lab in enumerate(labels):
        by_label[int(lab)].append(idx)

    results: list[ClusterResult] = []
    for lab, idxs in by_label.items():
        member_unit = unit[idxs]
        centroid = np.asarray(centroids[lab], dtype=float)
        m_texts = [texts[i] for i in idxs]
        total_weight = sum(weights[i] for i in idxs)
        weighted_sentiment = (
            sum(sentiments[i] * weights[i] for i in idxs) / total_weight
            if total_weight
            else 0.0
        )
        exemplars = nearest_exemplars(member_unit, centroid, m_texts, n=3)
        results.append(
            ClusterResult(
                member_indices=idxs,
                label=(exemplars[0][:120] if exemplars else None),
                summary="\n".join(f"- {e}" for e in exemplars),
                size=total_weight,
                sentiment=round(weighted_sentiment, 4),
                theme_kind=classify_theme(" ".join(exemplars), weighted_sentiment),
                centroid=centroid.tolist(),
            )
        )
    return results
