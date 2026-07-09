"""Billing domain: plan catalog, feature limits, and the Stripe gateway.

Design mirrors the AI gateway (``app/ai/llm.py``): a thin provider interface with a real
Stripe implementation and a deterministic offline **stub**, selected by whether a Stripe
secret key is configured. The stub lets the whole subscribe → checkout → webhook → gate
flow run in dev/preview with **zero** Stripe account and zero network calls.

Persistence lives elsewhere (``repositories/subscriptions.py``); this module only knows how
to *talk to Stripe* and how to *interpret Stripe objects* into our plan model. That keeps
the webhook handler free of Stripe-shape knowledge and makes the provider swappable.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

from ..config import Settings, get_settings


class Plan(str, enum.Enum):
    """The plans we sell. String-valued so it stores directly in ``subscriptions.plan``."""

    FREE = "free"
    PRO = "pro"
    AGENCY = "agency"


@dataclass(frozen=True)
class PlanLimits:
    """What a plan is allowed to do. This is the single source of truth for feature gating.

    Reasoning-tier cap is the cost lever: Free/Pro creators get cheaper models for reports,
    Agency unlocks the flagship monthly strategy call. Keeping the cap here means cost
    guardrails are declarative and testable, not scattered through the AI code.
    """

    plan: Plan
    max_channels: int
    monthly_report: bool          # flagship monthly strategy report
    max_reasoning_tier: str       # "cheap" | "standard" | "flagship"
    ai_chat: bool                 # streaming strategist chat
    seats: int                    # org members (agencies manage teams)
    label: str
    price_monthly_usd: int


PLAN_LIMITS: dict[Plan, PlanLimits] = {
    Plan.FREE: PlanLimits(
        plan=Plan.FREE,
        max_channels=1,
        monthly_report=False,
        max_reasoning_tier="cheap",
        ai_chat=False,
        seats=1,
        label="Free",
        price_monthly_usd=0,
    ),
    Plan.PRO: PlanLimits(
        plan=Plan.PRO,
        max_channels=3,
        monthly_report=True,
        max_reasoning_tier="standard",
        ai_chat=True,
        seats=1,
        label="Pro",
        price_monthly_usd=29,
    ),
    Plan.AGENCY: PlanLimits(
        plan=Plan.AGENCY,
        max_channels=25,
        monthly_report=True,
        max_reasoning_tier="flagship",
        ai_chat=True,
        seats=10,
        label="Agency",
        price_monthly_usd=99,
    ),
}


def limits_for(plan: str | Plan) -> PlanLimits:
    """Resolve limits for a plan value, defaulting to Free for unknown/legacy values."""
    try:
        return PLAN_LIMITS[Plan(plan)]
    except ValueError:
        return PLAN_LIMITS[Plan.FREE]


def plan_is_active(status: str) -> bool:
    """Stripe statuses we treat as entitling paid features. ``trialing`` counts as active."""
    return status in {"active", "trialing"}


def price_id_for_plan(plan: Plan, settings: Settings) -> str | None:
    return {
        Plan.PRO: settings.stripe_price_pro or None,
        Plan.AGENCY: settings.stripe_price_agency or None,
    }.get(plan)


def plan_for_price_id(price_id: str | None, settings: Settings) -> Plan:
    """Reverse map a Stripe price id back to our plan enum (used by the webhook)."""
    mapping = {
        settings.stripe_price_pro: Plan.PRO,
        settings.stripe_price_agency: Plan.AGENCY,
    }
    if price_id and price_id in mapping and mapping[price_id] is not None:
        return mapping[price_id]
    return Plan.FREE


# --- Provider interface ------------------------------------------------------------------


@dataclass(frozen=True)
class CheckoutSession:
    url: str
    session_id: str


@dataclass(frozen=True)
class PortalSession:
    url: str


@dataclass(frozen=True)
class SubscriptionState:
    """Normalized snapshot the webhook persists — provider-agnostic on purpose."""

    stripe_customer_id: str | None
    stripe_subscription_id: str | None
    plan: Plan
    status: str
    current_period_end: datetime | None


class BillingProvider(ABC):
    """Everything the app needs from a payments backend. Swappable + testable."""

    @abstractmethod
    async def create_checkout_session(
        self, *, organization_id: str, plan: Plan, customer_id: str | None, customer_email: str | None
    ) -> CheckoutSession: ...

    @abstractmethod
    async def create_portal_session(self, *, customer_id: str) -> PortalSession: ...

    @abstractmethod
    def parse_event_object(self, event_type: str, obj: dict) -> SubscriptionState | None:
        """Translate a Stripe webhook object into our normalized state (or None to ignore)."""


class StripeBillingProvider(BillingProvider):
    """Real Stripe. The ``stripe`` SDK is imported lazily so the app boots without it."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _client(self):
        import stripe  # lazy: only needed when a real key is configured

        stripe.api_key = self._settings.stripe_secret_key
        return stripe

    async def create_checkout_session(
        self, *, organization_id: str, plan: Plan, customer_id: str | None, customer_email: str | None
    ) -> CheckoutSession:
        price_id = price_id_for_plan(plan, self._settings)
        if not price_id:
            raise ValueError(f"No Stripe price configured for plan {plan.value}")
        stripe = self._client()
        params: dict = {
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": self._settings.billing_success_url,
            "cancel_url": self._settings.billing_cancel_url,
            # organization_id rides on metadata so the webhook can find the tenant even
            # before we know the Stripe customer id.
            "client_reference_id": organization_id,
            "subscription_data": {"metadata": {"organization_id": organization_id}},
            "metadata": {"organization_id": organization_id},
            "allow_promotion_codes": True,
        }
        if customer_id:
            params["customer"] = customer_id
        elif customer_email:
            params["customer_email"] = customer_email
        session = stripe.checkout.Session.create(**params)
        return CheckoutSession(url=session.url, session_id=session.id)

    async def create_portal_session(self, *, customer_id: str) -> PortalSession:
        stripe = self._client()
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=self._settings.billing_success_url,
        )
        return PortalSession(url=session.url)

    def parse_event_object(self, event_type: str, obj: dict) -> SubscriptionState | None:
        if event_type == "checkout.session.completed":
            # The session tells us customer + subscription ids; plan is confirmed by the
            # subsequent customer.subscription.* event, so mark active provisionally.
            return SubscriptionState(
                stripe_customer_id=obj.get("customer"),
                stripe_subscription_id=obj.get("subscription"),
                plan=Plan.FREE,  # refined by subscription events below
                status="active",
                current_period_end=None,
            )

        if event_type in {
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        }:
            items = (obj.get("items") or {}).get("data") or []
            price_id = items[0]["price"]["id"] if items else None
            status = "canceled" if event_type.endswith("deleted") else obj.get("status", "active")
            period_end = obj.get("current_period_end")
            return SubscriptionState(
                stripe_customer_id=obj.get("customer"),
                stripe_subscription_id=obj.get("id"),
                plan=plan_for_price_id(price_id, self._settings),
                status=status,
                current_period_end=(
                    datetime.fromtimestamp(period_end, tz=timezone.utc) if period_end else None
                ),
            )
        return None


class StubBillingProvider(BillingProvider):
    """Offline provider: deterministic fake URLs, no network, no Stripe account needed.

    Checkout returns a URL back into the app carrying the plan, so the dev/preview flow can
    simulate a successful subscription without leaving localhost.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def create_checkout_session(
        self, *, organization_id: str, plan: Plan, customer_id: str | None, customer_email: str | None
    ) -> CheckoutSession:
        url = (
            f"{self._settings.billing_success_url}"
            f"{'&' if '?' in self._settings.billing_success_url else '?'}"
            f"stub=1&plan={plan.value}&org={organization_id}"
        )
        return CheckoutSession(url=url, session_id=f"cs_stub_{organization_id}_{plan.value}")

    async def create_portal_session(self, *, customer_id: str) -> PortalSession:
        return PortalSession(
            url=f"{self._settings.billing_success_url}"
            f"{'&' if '?' in self._settings.billing_success_url else '?'}stub_portal=1"
        )

    def parse_event_object(self, event_type: str, obj: dict) -> SubscriptionState | None:
        # In stub mode the web app posts a synthetic {plan, organization_id} object.
        if event_type == "stub.checkout.completed":
            return SubscriptionState(
                stripe_customer_id=f"cus_stub_{obj.get('organization_id')}",
                stripe_subscription_id=f"sub_stub_{obj.get('organization_id')}",
                plan=Plan(obj.get("plan", "pro")),
                status="active",
                current_period_end=None,
            )
        return None


def get_billing_provider() -> BillingProvider:
    settings = get_settings()
    if settings.stripe_secret_key:
        return StripeBillingProvider(settings)
    return StubBillingProvider(settings)
