"""Background jobs run by the Arq worker.

Imports are slow (many YouTube API round-trips) and must never block an HTTP request, so
the OAuth callback enqueues `import_channel` and returns immediately. Each job owns its own
DB session and commits atomically.
"""

from __future__ import annotations

import logging
import uuid

from ..ai.reports import generate_channel_report
from ..db.session import SessionLocal
from ..services.importer import run_channel_import
from ..services.pipeline import run_comment_pipeline

logger = logging.getLogger("worker.jobs")


async def import_channel(ctx: dict, organization_id: str, channel_id: str) -> dict:
    """Fetch and store a channel's videos + comments, then queue comment processing."""
    client = ctx["http"]
    async with SessionLocal() as session:
        try:
            result = await run_channel_import(
                session,
                client,
                organization_id=uuid.UUID(organization_id),
                channel_id=uuid.UUID(channel_id),
            )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("channel import failed channel_id=%s", channel_id)
            raise
    logger.info("channel import complete: %s", result)

    # Chain: process the freshly imported comments (separate job = independent retry).
    await ctx["redis"].enqueue_job("process_channel_comments", organization_id, channel_id)
    return result


async def process_channel_comments(ctx: dict, organization_id: str, channel_id: str) -> dict:
    """Run the filter -> dedupe -> embed -> cluster pipeline over a channel's comments."""
    async with SessionLocal() as session:
        try:
            result = await run_comment_pipeline(
                session,
                organization_id=uuid.UUID(organization_id),
                channel_id=uuid.UUID(channel_id),
            )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("comment pipeline failed channel_id=%s", channel_id)
            raise
    logger.info("comment pipeline complete: %s", result)

    # Chain: generate the AI insight + strategy report from the fresh analysis.
    await ctx["redis"].enqueue_job(
        "generate_report", organization_id, channel_id, "weekly"
    )
    return result


async def generate_report(
    ctx: dict, organization_id: str, channel_id: str, kind: str = "weekly"
) -> dict:
    """Generate the AI insight + strategy report (scores → memory RAG → reasoning model)."""
    async with SessionLocal() as session:
        try:
            result = await generate_channel_report(
                session,
                organization_id=uuid.UUID(organization_id),
                channel_id=uuid.UUID(channel_id),
                kind=kind,
            )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("report generation failed channel_id=%s", channel_id)
            raise
    logger.info("report generation complete: %s", result)
    return result
