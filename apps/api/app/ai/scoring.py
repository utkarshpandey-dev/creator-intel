"""Channel scoring. Pure functions, zero LLM tokens.

Scores are deterministic heuristics computed from imported stats and the comment clusters —
they are cheap, explainable, and stable. The reasoning model later *interprets* these
numbers (why they moved, what to do); it never computes them.
"""

from __future__ import annotations

from datetime import datetime
from statistics import mean, pstdev


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return round(max(lo, min(hi, value)), 1)


def engagement_score(videos: list[dict]) -> float:
    """Average (likes + comments) / views across videos, mapped to 0–100."""
    ratios = []
    for v in videos:
        views = v.get("view_count") or 0
        if views <= 0:
            continue
        interactions = (v.get("like_count") or 0) + (v.get("comment_count") or 0)
        ratios.append(interactions / views)
    if not ratios:
        return 0.0
    # ~10% interaction rate maps to a top score.
    return _clamp(mean(ratios) * 1000)


def growth_score(videos: list[dict]) -> float:
    """Recent-vs-older average views. 1× → 50, 2× → 100."""
    dated = [v for v in videos if v.get("published_at") and v.get("view_count") is not None]
    if len(dated) < 4:
        return 50.0
    dated.sort(key=lambda v: v["published_at"])
    half = len(dated) // 2
    older = mean(v["view_count"] for v in dated[:half]) or 1
    newer = mean(v["view_count"] for v in dated[half:])
    return _clamp((newer / older) * 50)


def consistency_score(videos: list[dict]) -> float:
    """Upload-cadence regularity from the spread of gaps between uploads."""
    dates = sorted(v["published_at"] for v in videos if v.get("published_at"))
    if len(dates) < 3:
        return 50.0
    gaps = [
        (b - a).total_seconds() / 86400.0
        for a, b in zip(dates, dates[1:])
        if isinstance(a, datetime) and isinstance(b, datetime)
    ]
    gaps = [g for g in gaps if g >= 0]
    if not gaps:
        return 50.0
    avg = mean(gaps)
    if avg == 0:
        return 50.0
    cv = pstdev(gaps) / avg  # coefficient of variation; lower = more regular
    return _clamp(100 * (1 - cv))


def sentiment_score(clusters: list[dict]) -> float:
    """Size-weighted audience sentiment (-1..1) mapped to 0–100."""
    total = sum(c.get("size") or 0 for c in clusters)
    if total <= 0:
        return 50.0
    weighted = sum((c.get("sentiment") or 0.0) * (c.get("size") or 0) for c in clusters)
    return _clamp((weighted / total + 1) / 2 * 100)


def health_score(engagement: float, growth: float, consistency: float, sentiment: float) -> float:
    return _clamp(
        0.30 * engagement + 0.25 * growth + 0.20 * consistency + 0.25 * sentiment
    )


def _top(clusters: list[dict], kind: str, n: int = 5) -> list[dict]:
    matched = [c for c in clusters if c.get("theme_kind") == kind]
    matched.sort(key=lambda c: c.get("size") or 0, reverse=True)
    return [{"label": c.get("label"), "size": c.get("size"), "summary": c.get("summary")}
            for c in matched[:n]]


def build_scores(videos: list[dict], clusters: list[dict]) -> dict:
    eng = engagement_score(videos)
    grow = growth_score(videos)
    cons = consistency_score(videos)
    sent = sentiment_score(clusters)
    return {
        "health": health_score(eng, grow, cons, sent),
        "engagement": eng,
        "growth": grow,
        "consistency": cons,
        "sentiment": sent,
    }


def build_insight_payload(videos: list[dict], clusters: list[dict]) -> dict:
    """The structured, deterministic insight the reasoning model interprets."""
    by_sentiment = sorted(clusters, key=lambda c: (c.get("sentiment") or 0.0), reverse=True)
    return {
        "scores": build_scores(videos, clusters),
        "audience_requests": _top(clusters, "request"),
        "audience_complaints": _top(clusters, "complaint"),
        "best_topics": [
            {"label": c.get("label"), "size": c.get("size"), "sentiment": c.get("sentiment")}
            for c in by_sentiment[:5]
        ],
        "worst_topics": [
            {"label": c.get("label"), "size": c.get("size"), "sentiment": c.get("sentiment")}
            for c in by_sentiment[-5:] if (c.get("sentiment") or 0.0) < 0
        ],
        "video_count": len(videos),
        "theme_count": len(clusters),
    }
