"""Async engine, session factory, and the FastAPI DB dependency."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config import get_settings

_settings = get_settings()

# asyncpg needs ssl passed via connect_args, not the URL's ?sslmode= param.
_connect_args: dict = {"ssl": True} if _settings.db_require_ssl else {}

engine = create_async_engine(
    _settings.database_url,
    echo=_settings.db_echo,
    pool_pre_ping=True,  # transparently recycle connections dropped by Neon/pgbouncer
    connect_args=_connect_args,
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped session; commit on success, roll back on error."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
