"""Insight + strategy-report generation.

Flow: deterministic scores/themes (scoring.py, no LLM) → retrieve relevant creator memory
(RAG) → build a *compact* context (scores + top themes, never raw comments) → one reasoning
call (Sonnet for weekly, Opus for monthly) → persist Insight + Report + a new memory record.

Cost is bounded by the size of the summarized context, not the channel's comment volume.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import Channel, CommentCluster, Insight, Report, Video
from . import memory, scoring
from .llm import Tier, get_llm_provider

_SYSTEM = (
    "You are an elite YouTube growth strategist acting as a creator's second brain. "
    "You are given a compact, pre-computed analysis of a channel (scores, audience themes, "
    "requests, complaints, best/worst videos) and relevant history. Explain WHY performance "
    "looks the way it does, what the audience wants, what mistakes are repeating, and give "
    "specific, prioritized next actions. Be concrete and reference the data. Output Markdown."
)


def _video_dicts(videos: list[Video]) -> list[dict]:
    return [
        {
            "title": v.title,
            "view_count": v.view_count,
            "like_count": v.like_count,
            "comment_count": v.comment_count,
            "published_at": v.published_at,
        }
        for v in videos
    ]


def _cluster_dicts(clusters: list[CommentCluster]) -> list[dict]:
    return [
        {
            "label": c.label,
            "summary": c.summary,
            "size": c.size,
            "sentiment": c.sentiment,
            "theme_kind": c.theme_kind,
        }
        for c in clusters
    ]


def _engagement_ranked(videos: list[dict]) -> list[dict]:
    def ratio(v: dict) -> float:
        views = v.get("view_count") or 0
        if views <= 0:
            return 0.0
        return ((v.get("like_count") or 0) + (v.get("comment_count") or 0)) / views

    return sorted(videos, key=ratio, reverse=True)


def _build_context(title: str, payload: dict, ranked: list[dict], memories: list[str]) -> str:
    best = [f"- {v['title']} ({v.get('view_count') or 0} views)" for v in ranked[:5]]
    worst = [f"- {v['title']} ({v.get('view_count') or 0} views)" for v in ranked[-5:]]
    parts = [
        f"CHANNEL: {title}",
        f"SCORES (0-100): {json.dumps(payload['scores'])}",
        f"AUDIENCE REQUESTS: {json.dumps(payload['audience_requests'])}",
        f"AUDIENCE COMPLAINTS: {json.dumps(payload['audience_complaints'])}",
        f"BEST TOPICS: {json.dumps(payload['best_topics'])}",
        f"WORST TOPICS: {json.dumps(payload['worst_topics'])}",
        "BEST-ENGAGING VIDEOS:\n" + "\n".join(best),
        "WORST-ENGAGING VIDEOS:\n" + "\n".join(worst),
    ]
    if memories:
        parts.append("RELEVANT HISTORY (prior recommendations/observations):\n"
                      + "\n".join(f"- {m}" for m in memories))
    return "\n\n".join(parts)


async def generate_channel_report(
    session: AsyncSession,
    *,
    organization_id: uuid.UUID,
    channel_id: uuid.UUID,
    kind: str = "weekly",
) -> dict:
    settings = get_settings()
    channel = await session.get(Channel, channel_id)
    if channel is None or channel.organization_id != organization_id:
        raise ValueError("Channel not found for organization")

    videos = list(
        (await session.execute(select(Video).where(Video.channel_id == channel_id)))
        .scalars()
        .all()
    )
    clusters = list(
        (await session.execute(
            select(CommentCluster).where(CommentCluster.channel_id == channel_id)
        )).scalars().all()
    )

    video_dicts = _video_dicts(videos)
    cluster_dicts = _cluster_dicts(clusters)
    payload = scoring.build_insight_payload(video_dicts, cluster_dicts)

    # RAG: pull relevant prior memory for this channel.
    query = f"strategy, mistakes, and audience wants for {channel.title or 'this channel'}"
    prior = await memory.retrieve_memories(session, channel_id=channel_id, query=query)
    context = _build_context(
        channel.title or "Channel", payload, _engagement_ranked(video_dicts),
        [m.summary for m in prior],
    )

    tier = Tier.FLAGSHIP if kind == "monthly" else Tier.STANDARD
    prompt = (
        f"Produce a {kind} creator strategy report for this channel. "
        f"Structure it: Overview, Why performance looks like this, What the audience wants, "
        f"Mistakes to stop repeating, and a prioritized 30-day action plan.\n\n{context}"
    )
    llm = get_llm_provider()
    report_md = await llm.complete_text(system=_SYSTEM, user=prompt, tier=tier, max_tokens=4000)

    # Persist the structured insight, the human-readable report, and a memory record.
    dates = [v.published_at for v in videos if v.published_at]
    insight = Insight(
        organization_id=organization_id,
        channel_id=channel_id,
        kind="channel_analysis",
        period_start=min(dates) if dates else None,
        period_end=max(dates) if dates else None,
        payload=payload,
        model=None,
        prompt_version=settings.prompt_version,
    )
    report = Report(
        organization_id=organization_id,
        channel_id=channel_id,
        kind=kind,
        period_start=min(dates) if dates else None,
        period_end=max(dates) if dates else None,
        title=f"{kind.capitalize()} strategy report",
        content_md=report_md,
        payload={"scores": payload["scores"]},
        model=None,
    )
    session.add_all([insight, report])
    await session.flush()

    await memory.store_memory(
        session,
        organization_id=organization_id,
        channel_id=channel_id,
        kind="report_summary",
        summary=(
            f"{kind} report — health {payload['scores']['health']}, "
            f"top requests: {[r['label'] for r in payload['audience_requests'][:3]]}"
        ),
        meta={"report_id": str(report.id), "scores": payload["scores"]},
    )

    return {"insight_id": str(insight.id), "report_id": str(report.id), "scores": payload["scores"]}
