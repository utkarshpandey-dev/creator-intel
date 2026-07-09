"""Enqueue side of the worker: the API pushes jobs, the worker consumes them."""

from __future__ import annotations

import uuid

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from ..config import get_settings


async def get_arq_pool() -> ArqRedis:
    return await create_pool(RedisSettings.from_dsn(get_settings().redis_url))


async def _enqueue(job: str, organization_id: uuid.UUID, channel_id: uuid.UUID) -> None:
    pool = await get_arq_pool()
    try:
        await pool.enqueue_job(job, str(organization_id), str(channel_id))
    finally:
        await pool.close()


async def enqueue_channel_import(
    organization_id: uuid.UUID, channel_id: uuid.UUID
) -> None:
    await _enqueue("import_channel", organization_id, channel_id)


async def enqueue_comment_pipeline(
    organization_id: uuid.UUID, channel_id: uuid.UUID
) -> None:
    await _enqueue("process_channel_comments", organization_id, channel_id)


async def enqueue_report(
    organization_id: uuid.UUID, channel_id: uuid.UUID, kind: str = "weekly"
) -> None:
    pool = await get_arq_pool()
    try:
        await pool.enqueue_job(
            "generate_report", str(organization_id), str(channel_id), kind
        )
    finally:
        await pool.close()
