"""Billing endpoints: plan catalog, subscription status, Checkout & Portal, webhook sync.

Two audiences:
  * **User-facing** (Clerk-authenticated, org-scoped): read the current plan, start a
    Stripe Checkout to subscribe, or open the customer portal to manage/cancel.
  * **Internal** (shared-secret): receive Stripe events already signature-verified by the
    web app and persist them. Same trust model as the Clerk sync — the browser never writes
    subscription state; only signed webhooks do.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db
from ..deps import current_org, current_subscription, verify_internal_secret
from ..models import Organization, Subscription
from ..repositories import subscriptions as subs_repo
from ..services.billing import (
    PLAN_LIMITS,
    Plan,
    get_billing_provider,
    limits_for,
    plan_is_active,
)

router = APIRouter(prefix="/billing", tags=["billing"])


class PlanOut(BaseModel):
    plan: str
    label: str
    price_monthly_usd: int
    max_channels: int
    monthly_report: bool
    ai_chat: bool
    seats: int


class SubscriptionOut(BaseModel):
    plan: str
    status: str
    active: bool
    current_period_end: datetime | None
    limits: PlanOut


class CheckoutOut(BaseModel):
    url: str


def _plan_out(plan: Plan) -> PlanOut:
    lim = PLAN_LIMITS[plan]
    return PlanOut(
        plan=lim.plan.value,
        label=lim.label,
        price_monthly_usd=lim.price_monthly_usd,
        max_channels=lim.max_channels,
        monthly_report=lim.monthly_report,
        ai_chat=lim.ai_chat,
        seats=lim.seats,
    )


@router.get("/plans", response_model=list[PlanOut])
async def list_plans() -> list[PlanOut]:
    """The public plan catalog powering the pricing page."""
    return [_plan_out(p) for p in Plan]


@router.get("/subscription", response_model=SubscriptionOut)
async def get_subscription(
    sub: Subscription = Depends(current_subscription),
) -> SubscriptionOut:
    active = plan_is_active(sub.status)
    effective = limits_for(sub.plan if active else "free")
    return SubscriptionOut(
        plan=sub.plan,
        status=sub.status,
        active=active,
        current_period_end=sub.current_period_end,
        limits=_plan_out(effective.plan),
    )


@router.post("/checkout", response_model=CheckoutOut)
async def create_checkout(
    plan: str = Query(..., description="pro or agency"),
    org: Organization = Depends(current_org),
    sub: Subscription = Depends(current_subscription),
    db: AsyncSession = Depends(get_db),
) -> CheckoutOut:
    """Start a subscription. Returns a URL the browser redirects to (Stripe or stub)."""
    try:
        target = Plan(plan)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown plan") from exc
    if target == Plan.FREE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Free needs no checkout")

    provider = get_billing_provider()
    try:
        session = await provider.create_checkout_session(
            organization_id=str(org.id),
            plan=target,
            customer_id=sub.stripe_customer_id,
            customer_email=None,
        )
    except ValueError as exc:  # e.g. missing price id in prod config
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return CheckoutOut(url=session.url)


@router.post("/portal", response_model=CheckoutOut)
async def create_portal(
    sub: Subscription = Depends(current_subscription),
) -> CheckoutOut:
    """Open the Stripe customer portal to manage or cancel an existing subscription."""
    if not sub.stripe_customer_id:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "No billing account yet. Subscribe to a plan first."
        )
    provider = get_billing_provider()
    portal = await provider.create_portal_session(customer_id=sub.stripe_customer_id)
    return CheckoutOut(url=portal.url)


class StripeSyncIn(BaseModel):
    type: str
    data: dict[str, Any]


@router.post("/internal/stripe/sync", dependencies=[Depends(verify_internal_secret)])
async def stripe_sync(
    payload: StripeSyncIn, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """Apply a Stripe event already signature-verified by the web app.

    Resolves the tenant from checkout metadata (organization_id) or the Stripe customer id,
    then upserts the normalized subscription state. A 409 signals the web app to return
    non-2xx so Stripe redelivers until the tenant row exists.
    """
    provider = get_billing_provider()
    state = provider.parse_event_object(payload.type, payload.data)
    if state is None:
        return {"status": "ignored"}  # event we don't act on; ack so Stripe stops retrying

    org_id = None
    meta = payload.data.get("metadata") or {}
    raw_org = meta.get("organization_id") or payload.data.get("organization_id") or payload.data.get(
        "client_reference_id"
    )
    if raw_org:
        import uuid

        try:
            org_id = uuid.UUID(raw_org)
        except ValueError:
            org_id = None

    sub = await subs_repo.apply_state(db, organization_id=org_id, state=state)
    if sub is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Tenant for this billing event not found yet."
        )
    await db.commit()
    return {"status": "applied", "plan": sub.plan, "subscription_status": sub.status}
