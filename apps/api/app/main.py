"""FastAPI application entrypoint.

Milestone 2 scope: a secure, multi-tenant front door.
  - GET  /health                 liveness (public)
  - GET  /me                     returns the verified caller's identity (auth required)
  - GET  /orgs/current           requires an active org (tenant-scoped example)
  - POST /internal/clerk/sync    receives verified Clerk events from the web app
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from . import clerk_sync
from .auth import Identity
from .config import get_settings
from .db.session import get_db
from .deps import current_identity, require_org, verify_internal_secret
from .routers import analysis, billing, chat, youtube

settings = get_settings()
logger = logging.getLogger("creator_intel.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Fail fast on unsafe production config before we ever accept a request.
    settings.validate_for_deploy()
    logger.info("creator-intel API starting (env=%s)", settings.app_env)
    yield


app = FastAPI(title="creator-intel API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(youtube.router)
app.include_router(analysis.router)
app.include_router(chat.router)
app.include_router(billing.router)


class IdentityOut(BaseModel):
    user_id: str
    org_id: str | None
    org_role: str | None


class ClerkSyncIn(BaseModel):
    type: str
    data: dict[str, Any]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Readiness probe that confirms the database is reachable."""
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "reachable"}


@app.get("/me", response_model=IdentityOut)
async def me(identity: Identity = Depends(current_identity)) -> Identity:
    """Echo the authenticated identity. Proves end-to-end token verification."""
    return identity


@app.get("/orgs/current", response_model=IdentityOut)
async def current_org(identity: Identity = Depends(require_org)) -> Identity:
    """Example tenant-scoped endpoint: 403s unless an org context is present."""
    return identity


@app.post("/internal/clerk/sync", dependencies=[Depends(verify_internal_secret)])
async def clerk_sync_endpoint(
    payload: ClerkSyncIn, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """Apply a Clerk event already signature-verified by the web app."""
    try:
        await clerk_sync.apply_event(db, payload.type, payload.data)
    except LookupError as exc:
        # Event arrived before its dependency was mirrored. 409 → the web app returns
        # non-2xx to Clerk, which redelivers with backoff until it reconciles.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {"status": "applied"}
