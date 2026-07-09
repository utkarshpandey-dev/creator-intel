"""Stage 2 — near-duplicate collapse. Pure code, zero LLM tokens.

Exact collapse on the normalized content_hash: "Great video!!!", "great video", and
"GREAT VIDEO" share a hash (see importer._content_hash), so thousands of identical reactions
become one weighted record — massively cutting how many comments we embed and cluster.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TypeVar

T = TypeVar("T")


def group_by_hash(items: list[tuple[T, str]]) -> dict[str, list[T]]:
    """Map content_hash -> list of item keys sharing it, preserving input order."""
    groups: dict[str, list[T]] = defaultdict(list)
    for key, content_hash in items:
        groups[content_hash].append(key)
    return dict(groups)
