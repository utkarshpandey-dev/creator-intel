"""Tenant-scoped repository base.

Every query for tenant-owned data must be filtered by organization_id. Centralizing that
here — instead of trusting each call site to remember — is our primary defense against
cross-tenant data leaks. Feature repositories subclass this and never issue an unscoped
query for tenant data.
"""

from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class TenantRepository(Generic[ModelT]):
    """Base repo bound to a single organization. All reads/writes are org-scoped."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession, organization_id: uuid.UUID) -> None:
        self.session = session
        self.organization_id = organization_id

    def _scoped(self):
        # Assumes the model has an organization_id column. Tenant models all do.
        return select(self.model).where(
            self.model.organization_id == self.organization_id  # type: ignore[attr-defined]
        )

    async def get(self, obj_id: uuid.UUID) -> ModelT | None:
        result = await self.session.execute(self._scoped().where(self.model.id == obj_id))
        return result.scalar_one_or_none()

    async def list(self, limit: int = 100, offset: int = 0) -> list[ModelT]:
        result = await self.session.execute(self._scoped().limit(limit).offset(offset))
        return list(result.scalars().all())

    async def add(self, obj: ModelT) -> ModelT:
        # Enforce the tenant on write, so a caller can't insert into another org.
        setattr(obj, "organization_id", self.organization_id)
        self.session.add(obj)
        await self.session.flush()
        return obj
