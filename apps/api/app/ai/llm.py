"""Tiered Claude gateway.

Business logic depends on the LLMProvider interface and a task *tier*, never a concrete
model id — so routing Haiku→Sonnet→Opus is a config concern, and we can swap providers
without touching callers. A deterministic stub stands in when no API key is set, so the AI
engine (reports, memory, chat) runs end-to-end offline with zero cost.

Tiering (see ARCHITECTURE.md § Model tiering):
  CHEAP     → Haiku   : labels, quick summaries
  STANDARD  → Sonnet  : weekly reports
  FLAGSHIP  → Opus    : monthly strategy, chat reasoning
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from ..config import get_settings


class Tier(enum.Enum):
    CHEAP = "cheap"
    STANDARD = "standard"
    FLAGSHIP = "flagship"


def _model_for(tier: Tier) -> str:
    s = get_settings()
    return {
        Tier.CHEAP: s.model_cheap,
        Tier.STANDARD: s.model_standard,
        Tier.FLAGSHIP: s.model_flagship,
    }[tier]


class LLMProvider(ABC):
    @abstractmethod
    async def complete_text(
        self, *, system: str, user: str, tier: Tier, max_tokens: int = 4000
    ) -> str: ...

    @abstractmethod
    def stream_text(
        self, *, system: str, messages: list[dict], tier: Tier, max_tokens: int = 4000
    ) -> AsyncIterator[str]: ...


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str) -> None:
        from anthropic import AsyncAnthropic  # imported lazily so the stub needs no dep

        self._client = AsyncAnthropic(api_key=api_key)

    def _thinking(self, tier: Tier) -> dict | None:
        # Adaptive thinking on the flagship reasoning tier; off for cheap extraction.
        return {"type": "adaptive"} if tier is Tier.FLAGSHIP else None

    async def complete_text(
        self, *, system: str, user: str, tier: Tier, max_tokens: int = 4000
    ) -> str:
        kwargs: dict = {
            "model": _model_for(tier),
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        if (thinking := self._thinking(tier)) is not None:
            kwargs["thinking"] = thinking
        resp = await self._client.messages.create(**kwargs)
        return "".join(b.text for b in resp.content if b.type == "text")

    async def stream_text(
        self, *, system: str, messages: list[dict], tier: Tier, max_tokens: int = 4000
    ) -> AsyncIterator[str]:
        async with self._client.messages.stream(
            model=_model_for(tier),
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text


class StubLLMProvider(LLMProvider):
    """Offline provider. Deterministic, no API cost, no semantic quality — dev/tests only."""

    async def complete_text(
        self, *, system: str, user: str, tier: Tier, max_tokens: int = 4000
    ) -> str:
        head = user.strip().splitlines()[0] if user.strip() else "(no input)"
        return (
            f"[stub:{tier.value}] Draft response based on the provided context.\n\n"
            f"Context begins with: {head[:200]}"
        )

    async def stream_text(
        self, *, system: str, messages: list[dict], tier: Tier, max_tokens: int = 4000
    ) -> AsyncIterator[str]:
        last = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
        )
        if isinstance(last, list):  # content blocks
            last = " ".join(b.get("text", "") for b in last if isinstance(b, dict))
        for chunk in (
            f"[stub:{tier.value}] ",
            "Here is a channel-grounded answer to: ",
            str(last)[:160],
        ):
            yield chunk


def get_llm_provider() -> LLMProvider:
    key = get_settings().anthropic_api_key
    return AnthropicProvider(key) if key else StubLLMProvider()
