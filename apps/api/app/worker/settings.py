"""Arq worker entrypoint.

Run with:  arq app.worker.settings.WorkerSettings
"""

from __future__ import annotations

import httpx
from arq.connections import RedisSettings

from ..config import get_settings
from .jobs import generate_report, import_channel, process_channel_comments

_settings = get_settings()


async def on_startup(ctx: dict) -> None:
    # Refuse to process jobs under an unsafe production configuration (same guard as the API).
    _settings.validate_for_deploy()
    # One shared HTTP client per worker process (connection pooling for the YouTube API).
    ctx["http"] = httpx.AsyncClient(timeout=30.0)


async def on_shutdown(ctx: dict) -> None:
    await ctx["http"].aclose()


class WorkerSettings:
    functions = [import_channel, process_channel_comments, generate_report]
    on_startup = on_startup
    on_shutdown = on_shutdown
    redis_settings = RedisSettings.from_dsn(_settings.redis_url)
    max_jobs = 5  # bound concurrency to stay within YouTube quota
    job_timeout = 60 * 15  # long-running imports
