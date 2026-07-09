"""Persistence for the ``subscriptions`` table — the source of truth for feature gating.

The webhook applier and the gating dependencies are the only callers. Everything is keyed
by our internal ``organization_id`` (tenant isolation), with a secondary lookup by Stripe
customer id so subscription events — which don't carry our org id directly — can find the
right tenant.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Subscription
from ..services.billing import SubscriptionState, plan_is_active


async def get_by_org(session: AsyncSession, organization_id: uuid.UUID) -> Subscription | None:
    res = await session.execute(
        select(Subscription).where(Subscription.organization_id == organization_id)
    )
    return res.scalar_one_or_none()


async def get_by_customer(session: AsyncSession, stripe_customer_id: str) -> Subscription | None:
    res = await session.execute(
        select(Subscription).where(Subscription.stripe_customer_id == stripe_customer_id)
    )
    return res.scalar_one_or_none()


async def get_or_create_free(
    session: AsyncSession, organization_id: uuid.UUID
) -> Subscription:
    """Every org has a subscription row; absent one, it's implicitly Free.

    Lazily materializing it keeps gating logic simple (always has a row to read) without a
    backfill migration for orgs created before billing existed.
    """
    sub = await get_by_org(session, organization_id)
    if sub is None:
        sub = Subscription(organization_id=organization_id, plan="free", status="inactive")
        session.add(sub)
        await session.flush()
    return sub


async def apply_state(
    session: AsyncSession,
    *,
    organization_id: uuid.UUID | None,
    state: SubscriptionState,
) -> Subscription | None:
    """Idempotently upsert normalized Stripe state onto the org's subscription row.

    Resolves the tenant by explicit ``organization_id`` (from checkout metadata) first, then
    falls back to the Stripe customer id (for later subscription.* events). Returns None if
    the tenant can't be resolved — the caller surfaces a 409 so Stripe retries.
    """
    sub: Subscription | None = None
    if organization_id is not None:
        sub = await get_or_create_free(session, organization_id)
    elif state.stripe_customer_id:
        sub = await get_by_customer(session, state.stripe_customer_id)

    if sub is None:
        return None

    if state.stripe_customer_id:
        sub.stripe_customer_id = state.stripe_customer_id
    if state.stripe_subscription_id:
        sub.stripe_subscription_id = state.stripe_subscription_id
    # checkout.session.completed carries no price → don't downgrade a plan we already know.
    if state.plan.value != "free" or not plan_is_active(sub.status):
        sub.plan = state.plan.value
    sub.status = state.status
    if state.current_period_end is not None:
        sub.current_period_end = state.current_period_end

    # A canceled/expired subscription reverts entitlements to Free.
    if not plan_is_active(sub.status):
        sub.plan = "free"

    await session.flush()
    return sub
