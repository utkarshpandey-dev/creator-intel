"""Unit tests for the AI engine's pure/offline pieces (scoring + gateway stub)."""

import asyncio
import os
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet

os.environ.setdefault("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("INTERNAL_API_SECRET", "test-internal-secret")
os.environ.pop("ANTHROPIC_API_KEY", None)  # force the offline stub

from app.ai import scoring  # noqa: E402
from app.ai.llm import (  # noqa: E402
    AnthropicProvider,
    StubLLMProvider,
    Tier,
    _model_for,
    get_llm_provider,
)


def _video(views, likes, comments, day):
    return {
        "view_count": views,
        "like_count": likes,
        "comment_count": comments,
        "published_at": datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=day),
    }


# --- scoring ---
def test_engagement_score_scales_with_interaction_rate():
    low = scoring.engagement_score([_video(1000, 5, 5, 0)])      # 1% → 10
    high = scoring.engagement_score([_video(1000, 60, 40, 0)])   # 10% → 100
    assert high > low
    assert 0 <= low <= 100 and 0 <= high <= 100


def test_growth_score_detects_growth_and_decline():
    growing = [_video(100, 1, 1, i) for i in range(4)] + [_video(400, 1, 1, i + 4) for i in range(4)]
    declining = [_video(400, 1, 1, i) for i in range(4)] + [_video(100, 1, 1, i + 4) for i in range(4)]
    assert scoring.growth_score(growing) > 50
    assert scoring.growth_score(declining) < 50


def test_consistency_score_rewards_regular_cadence():
    regular = [_video(100, 1, 1, i * 7) for i in range(6)]      # every 7 days
    erratic = [_video(100, 1, 1, d) for d in (0, 1, 2, 30, 31, 90)]
    assert scoring.consistency_score(regular) > scoring.consistency_score(erratic)


def test_sentiment_score_and_payload():
    clusters = [
        {"size": 100, "sentiment": 0.8, "theme_kind": "praise", "label": "great edits"},
        {"size": 50, "sentiment": -0.6, "theme_kind": "complaint", "label": "audio bad"},
        {"size": 30, "sentiment": 0.1, "theme_kind": "request", "label": "make part 2"},
    ]
    assert 0 <= scoring.sentiment_score(clusters) <= 100
    payload = scoring.build_insight_payload([_video(1000, 50, 50, 0)], clusters)
    assert set(payload["scores"]) == {"health", "engagement", "growth", "consistency", "sentiment"}
    assert payload["audience_requests"][0]["label"] == "make part 2"
    assert payload["audience_complaints"][0]["label"] == "audio bad"


def test_empty_inputs_do_not_crash():
    payload = scoring.build_insight_payload([], [])
    assert payload["scores"]["health"] >= 0


# --- gateway ---
def test_tier_maps_to_configured_models():
    assert _model_for(Tier.CHEAP) == "claude-haiku-4-5"
    assert _model_for(Tier.STANDARD) == "claude-sonnet-5"
    assert _model_for(Tier.FLAGSHIP) == "claude-opus-4-8"


def test_provider_falls_back_to_stub_without_key():
    assert isinstance(get_llm_provider(), StubLLMProvider)


def test_stub_complete_text_is_deterministic():
    stub = StubLLMProvider()
    a = asyncio.run(stub.complete_text(system="s", user="analyze this channel", tier=Tier.STANDARD))
    b = asyncio.run(stub.complete_text(system="s", user="analyze this channel", tier=Tier.STANDARD))
    assert a == b and "stub" in a


def test_stub_stream_yields_chunks():
    stub = StubLLMProvider()

    async def collect():
        return [c async for c in stub.stream_text(
            system="s", messages=[{"role": "user", "content": "why did my video fail?"}],
            tier=Tier.FLAGSHIP,
        )]

    chunks = asyncio.run(collect())
    assert len(chunks) >= 1
    assert "why did my video fail?" in "".join(chunks)


def test_anthropic_provider_thinking_tiering():
    # Constructing the provider doesn't call the API; check tier→thinking policy.
    provider = AnthropicProvider(api_key="sk-test")
    assert provider._thinking(Tier.FLAGSHIP) == {"type": "adaptive"}
    assert provider._thinking(Tier.CHEAP) is None
