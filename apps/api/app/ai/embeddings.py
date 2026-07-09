"""Pluggable embedding providers.

The rest of the system depends on the EmbeddingProvider interface, never a concrete vendor,
so we can swap OpenAI for Voyage/Cohere/local without touching the pipeline. A deterministic
provider is used offline (and in tests) so the full pipeline runs with zero API cost.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

import httpx
import numpy as np

from ..config import get_settings


class EmbeddingProvider(ABC):
    dim: int

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in order."""


class DeterministicEmbeddingProvider(EmbeddingProvider):
    """Offline/dev provider. Same text -> same vector, semantically meaningless but stable.

    Good enough to exercise caching, clustering, and representative selection without an API
    key. Never use in production — it has no semantic signal.
    """

    def __init__(self, dim: int) -> None:
        self.dim = dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
            rng = np.random.default_rng(seed)
            v = rng.standard_normal(self.dim)
            v /= np.linalg.norm(v) or 1.0
            vectors.append(v.astype(float).tolist())
        return vectors


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, base_url: str, model: str, dim: int) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self.dim = dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self._base_url}/embeddings",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._model, "input": texts, "dimensions": self.dim},
            )
            resp.raise_for_status()
            data = resp.json()["data"]
        # API preserves input order via the `index` field; sort to be safe.
        ordered = sorted(data, key=lambda d: d["index"])
        return [item["embedding"] for item in ordered]


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    dim = settings.embedding_dim
    if settings.embedding_provider == "openai" and settings.openai_api_key:
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.embedding_model,
            dim=dim,
        )
    # No key configured → deterministic so the pipeline still runs locally.
    return DeterministicEmbeddingProvider(dim=dim)
