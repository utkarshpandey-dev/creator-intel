"""FastAPI dependencies for authentication and multi-tenant scoping."""

from __future__ import annotations

import hmac

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import AuthError, Identity, verify_token
from .config import get_settings
from .db.session import get_db
from .models import Organization, Subscription
from .repositories.tenant import get_organization_by_clerk_id
from .repositories import subscriptions as subs_repo
from .services.billing import PlanLimits, limits_for, plan_is_active


async def current_identity(
    authorization: str | None = Header(default=None),
) -> Identity:
    """Resolve the authenticated caller from the Bearer token, or 401."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        return verify_token(token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def require_org(identity: Identity = Depends(current_identity)) -> Identity:
    """Require an active organization context.

    Every tenant-scoped resource (channels, insights, memory) hangs off an org. Endpoints
    that touch tenant data depend on this so the org id is guaranteed present and comes
    only from a verified token — the basis of our row-level tenant isolation.
    """
    if not identity.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active organization. Select or create a workspace first.",
        )
    return identity


async def current_org(
    identity: Identity = Depends(require_org),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """Resolve the Clerk org id from the token to our internal Organization row.

    Repositories scope by our UUID primary key, not Clerk's string id, so every
    tenant-data endpoint depends on this. A 409 here means the org exists in Clerk but the
    webhook mirror hasn't landed yet (rare, self-heals on Clerk's retry).
    """
    org = await get_organization_by_clerk_id(db, identity.org_id)  # type: ignore[arg-type]
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization is not yet provisioned. Please retry shortly.",
        )
    return org


async def current_subscription(
    org: Organization = Depends(current_org),
    db: AsyncSession = Depends(get_db),
) -> Subscription:
    """The org's subscription row (materializing a Free one if none exists yet)."""
    return await subs_repo.get_or_create_free(db, org.id)


async def current_plan_limits(
    sub: Subscription = Depends(current_subscription),
) -> PlanLimits:
    """Effective feature limits for the caller's org — Free unless a plan is active."""
    if plan_is_active(sub.status):
        return limits_for(sub.plan)
    return limits_for("free")


def require_feature(feature: str):
    """Dependency factory gating a boolean plan feature (e.g. ``ai_chat``).

    Usage: ``_: None = Depends(require_feature("ai_chat"))``. Returns 402 Payment Required
    so the web app can route the user to the pricing page rather than showing a hard error.
    """

    async def _guard(limits: PlanLimits = Depends(current_plan_limits)) -> None:
        if not getattr(limits, feature, False):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Your plan ({limits.label}) doesn't include this feature. Upgrade to continue.",
            )

    return _guard


async def verify_internal_secret(x_internal_secret: str | None = Header(default=None)) -> None:
    """Guard internal-only endpoints (e.g. Clerk webhook forwarding from the web app)."""
    expected = get_settings().internal_api_secret
    if not x_internal_secret or not hmac.compare_digest(x_internal_secret, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")
