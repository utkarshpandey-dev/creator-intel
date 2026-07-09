"""Creator memory — the RAG layer that makes advice compound over time.

Each report/recommendation/observation is embedded and stored. When generating a new report
or answering a chat question, we retrieve only the *semantically relevant* past memories and
feed those to the model — so month 3 is smarter than month 1 without resending all history.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import MemoryRecord
from .embeddings import get_embedding_provider


async def store_memory(
    session: AsyncSession,
    *,
    organization_id: uuid.UUID,
    channel_id: uuid.UUID,
    kind: str,
    summary: str,
    meta: dict | None = None,
) -> MemoryRecord:
    provider = get_embedding_provider()
    vector = (await provider.embed([summary]))[0]
    record = MemoryRecord(
        organization_id=organization_id,
        channel_id=channel_id,
        kind=kind,
        summary=summary,
        meta=meta,
        vector=vector,
    )
    session.add(record)
    await session.flush()
    return record


async def retrieve_memories(
    session: AsyncSession,
    *,
    channel_id: uuid.UUID,
    query: str,
    k: int | None = None,
) -> list[MemoryRecord]:
    k = k or get_settings().memory_top_k
    provider = get_embedding_provider()
    query_vec = (await provider.embed([query]))[0]
    # pgvector cosine distance; nearest first. Only rows with a stored vector.
    stmt = (
        select(MemoryRecord)
        .where(MemoryRecord.channel_id == channel_id, MemoryRecord.vector.is_not(None))
        .order_by(MemoryRecord.vector.cosine_distance(query_vec))
        .limit(k)
    )
    return list((await session.execute(stmt)).scalars().all())
