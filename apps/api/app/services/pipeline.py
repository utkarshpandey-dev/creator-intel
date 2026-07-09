"""Comment processing orchestrator (Milestone 5).

Runs the cost-optimization pipeline over a channel's imported comments:

    filter  ->  near-duplicate collapse  ->  sentiment  ->  cached embeddings
            ->  clustering  ->  representative selection

Output: weighted, de-duplicated comments assigned to theme clusters, each cluster carrying
exemplars + sentiment + kind. That compact result is what the AI engine (M6) reasons over —
no raw comments reach the reasoning model. The only external cost here is embeddings, and
those are cached by content_hash so re-runs are nearly free.

Idempotent: safe to re-run; it recomputes flags/weights and rebuilds clusters from scratch.

Note: loads a channel's comments into memory. Fine within the import caps; for very large
channels this becomes a batched/streamed job (tracked as a scaling follow-up).
"""

from __future__ import annotations

import uuid

import numpy as np
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..ai.embeddings import get_embedding_provider
from ..config import get_settings
from ..models import Comment, CommentCluster, Embedding
from ..pipeline import filtering, sentiment
from ..pipeline.assembly import assemble_clusters
from ..pipeline.dedupe import group_by_hash


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


async def run_comment_pipeline(
    session: AsyncSession, *, organization_id: uuid.UUID, channel_id: uuid.UUID
) -> dict:
    settings = get_settings()

    comments = list(
        (await session.execute(select(Comment).where(Comment.channel_id == channel_id)))
        .scalars()
        .all()
    )
    if not comments:
        return {"total": 0, "kept": 0, "representatives": 0, "clusters": 0, "embedded_new": 0}

    # --- Stage 1: filter ---
    for c in comments:
        c.kept = filtering.should_keep(c.text, min_words=settings.min_comment_words)
    kept = [c for c in comments if c.kept]

    # --- Stage 2: near-duplicate collapse ---
    groups = group_by_hash([(c, c.content_hash) for c in kept])
    representatives: list[Comment] = []
    for group in groups.values():
        rep = group[0]
        rep.weight = len(group)
        rep.kept = True
        for dup in group[1:]:
            dup.kept = False
            dup.cluster_id = None
        representatives.append(rep)

    # --- Stage 3: sentiment (representatives only) ---
    for c in representatives:
        c.sentiment = sentiment.score(c.text)

    # --- Stage 4a: embeddings, served from cache where possible ---
    hashes = [c.content_hash for c in representatives]
    cached = {
        h: np.asarray(v, dtype=float)
        for h, v in (
            await session.execute(
                select(Embedding.content_hash, Embedding.vector).where(
                    Embedding.channel_id == channel_id, Embedding.content_hash.in_(hashes)
                )
            )
        ).all()
    }
    missing = [c for c in representatives if c.content_hash not in cached]
    provider = get_embedding_provider()
    embedded_new = 0
    for batch in _chunks(missing, settings.embedding_batch_size):
        vectors = await provider.embed([c.text for c in batch])
        for c, vec in zip(batch, vectors):
            cached[c.content_hash] = np.asarray(vec, dtype=float)
            session.add(
                Embedding(
                    organization_id=organization_id,
                    channel_id=channel_id,
                    content_hash=c.content_hash,
                    model=settings.embedding_model,
                    vector=vec,
                )
            )
            embedded_new += 1
    await session.flush()

    # --- Stage 4b + 5: cluster and select exemplars ---
    # Rebuild clusters from scratch (FK ON DELETE SET NULL clears stale comment links).
    await session.execute(
        delete(CommentCluster).where(CommentCluster.channel_id == channel_id)
    )
    await session.flush()
    for c in representatives:
        c.cluster_id = None

    n = len(representatives)
    if n == 0:
        await session.flush()
        return {
            "total": len(comments),
            "kept": len(kept),
            "representatives": 0,
            "clusters": 0,
            "embedded_new": embedded_new,
        }

    matrix = np.vstack([cached[c.content_hash] for c in representatives])
    results = assemble_clusters(
        texts=[c.text for c in representatives],
        weights=[c.weight for c in representatives],
        sentiments=[c.sentiment or 0.0 for c in representatives],
        vectors=matrix,
        max_clusters=settings.max_clusters,
        min_comments_to_cluster=settings.min_comments_to_cluster,
    )

    for result in results:
        cluster = CommentCluster(
            channel_id=channel_id,
            label=result.label,
            summary=result.summary,
            size=result.size,
            sentiment=result.sentiment,
            theme_kind=result.theme_kind,
            centroid=result.centroid,
        )
        session.add(cluster)
        await session.flush()  # obtain cluster.id
        for i in result.member_indices:
            representatives[i].cluster_id = cluster.id

    await session.flush()
    clusters_created = len(results)
    return {
        "total": len(comments),
        "kept": len(kept),
        "representatives": n,
        "clusters": clusters_created,
        "embedded_new": embedded_new,
    }
