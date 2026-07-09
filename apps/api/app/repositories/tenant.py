"""Lookups that bridge Clerk's string ids to our internal tenant rows."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Organization


async def get_organization_by_clerk_id(
    session: AsyncSession, clerk_org_id: str
) -> Organization | None:
    res = await session.execute(
        select(Organization).where(Organization.clerk_org_id == clerk_org_id)
    )
    return res.scalar_one_or_none()
