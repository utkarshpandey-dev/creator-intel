"""Idempotent upserts that mirror Clerk identity into Postgres.

Clerk can redeliver webhooks, so every operation is written with ON CONFLICT to be safe to
apply more than once. Memberships resolve Clerk's string ids to our internal UUIDs.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Membership, Organization, User


async def upsert_user(
    session: AsyncSession,
    *,
    clerk_user_id: str,
    email: str | None,
    first_name: str | None,
    last_name: str | None,
    image_url: str | None,
) -> None:
    stmt = insert(User).values(
        clerk_user_id=clerk_user_id,
        email=email,
        first_name=first_name,
        last_name=last_name,
        image_url=image_url,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[User.clerk_user_id],
        set_={
            "email": stmt.excluded.email,
            "first_name": stmt.excluded.first_name,
            "last_name": stmt.excluded.last_name,
            "image_url": stmt.excluded.image_url,
            "updated_at": datetime.now(timezone.utc),
        },
    )
    await session.execute(stmt)


async def delete_user(session: AsyncSession, *, clerk_user_id: str) -> None:
    user = await _user_by_clerk_id(session, clerk_user_id)
    if user is not None:
        await session.delete(user)  # cascades to memberships


async def upsert_organization(
    session: AsyncSession, *, clerk_org_id: str, name: str, slug: str | None
) -> None:
    stmt = insert(Organization).values(clerk_org_id=clerk_org_id, name=name, slug=slug)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Organization.clerk_org_id],
        set_={
            "name": stmt.excluded.name,
            "slug": stmt.excluded.slug,
            "updated_at": datetime.now(timezone.utc),
        },
    )
    await session.execute(stmt)


async def delete_organization(session: AsyncSession, *, clerk_org_id: str) -> None:
    org = await _org_by_clerk_id(session, clerk_org_id)
    if org is not None:
        await session.delete(org)  # cascades to memberships, channels, and tenant data


async def add_membership(
    session: AsyncSession, *, clerk_org_id: str, clerk_user_id: str, role: str
) -> None:
    org = await _org_by_clerk_id(session, clerk_org_id)
    user = await _user_by_clerk_id(session, clerk_user_id)
    if org is None or user is None:
        # Ordering isn't guaranteed; a later org/user event + Clerk retry will reconcile.
        raise LookupError("org or user not yet mirrored; will retry on redelivery")

    stmt = insert(Membership).values(
        organization_id=org.id, user_id=user.id, role=role
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[Membership.organization_id, Membership.user_id],
        set_={"role": stmt.excluded.role, "updated_at": datetime.now(timezone.utc)},
    )
    await session.execute(stmt)


async def remove_membership(
    session: AsyncSession, *, clerk_org_id: str, clerk_user_id: str
) -> None:
    org = await _org_by_clerk_id(session, clerk_org_id)
    user = await _user_by_clerk_id(session, clerk_user_id)
    if org is None or user is None:
        return
    existing = await session.execute(
        select(Membership).where(
            Membership.organization_id == org.id, Membership.user_id == user.id
        )
    )
    membership = existing.scalar_one_or_none()
    if membership is not None:
        await session.delete(membership)


async def _org_by_clerk_id(session: AsyncSession, clerk_org_id: str) -> Organization | None:
    res = await session.execute(
        select(Organization).where(Organization.clerk_org_id == clerk_org_id)
    )
    return res.scalar_one_or_none()


async def _user_by_clerk_id(session: AsyncSession, clerk_user_id: str) -> User | None:
    res = await session.execute(select(User).where(User.clerk_user_id == clerk_user_id))
    return res.scalar_one_or_none()
