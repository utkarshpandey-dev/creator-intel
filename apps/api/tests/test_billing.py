"""Unit tests for Milestone 8 billing: plan catalog, price mapping, webhook parsing,
and the offline stub provider — all runnable with zero Stripe account."""

import asyncio
import os
from datetime import datetime, timezone

from cryptography.fernet import Fernet

os.environ.setdefault("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("INTERNAL_API_SECRET", "test-internal-secret")
os.environ.pop("STRIPE_SECRET_KEY", None)  # force the offline stub

from app.config import get_settings  # noqa: E402
from app.services.billing import (  # noqa: E402
    PLAN_LIMITS,
    Plan,
    StripeBillingProvider,
    StubBillingProvider,
    get_billing_provider,
    limits_for,
    plan_for_price_id,
    plan_is_active,
)


def test_plan_catalog_covers_all_plans():
    assert set(PLAN_LIMITS) == {Plan.FREE, Plan.PRO, Plan.AGENCY}
    # Cost lever escalates with price.
    assert PLAN_LIMITS[Plan.FREE].max_reasoning_tier == "cheap"
    assert PLAN_LIMITS[Plan.AGENCY].max_reasoning_tier == "flagship"
    assert PLAN_LIMITS[Plan.FREE].max_channels < PLAN_LIMITS[Plan.AGENCY].max_channels


def test_limits_for_unknown_defaults_free():
    assert limits_for("enterprise-typo").plan == Plan.FREE
    assert limits_for("pro").plan == Plan.PRO


def test_plan_is_active():
    assert plan_is_active("active")
    assert plan_is_active("trialing")
    assert not plan_is_active("canceled")
    assert not plan_is_active("inactive")


def test_price_id_reverse_mapping():
    settings = get_settings()
    object.__setattr__(settings, "stripe_price_pro", "price_pro_123")
    object.__setattr__(settings, "stripe_price_agency", "price_agency_456")
    assert plan_for_price_id("price_pro_123", settings) == Plan.PRO
    assert plan_for_price_id("price_agency_456", settings) == Plan.AGENCY
    assert plan_for_price_id("price_unknown", settings) == Plan.FREE
    assert plan_for_price_id(None, settings) == Plan.FREE


def test_get_provider_is_stub_without_key():
    assert isinstance(get_billing_provider(), StubBillingProvider)


def test_stub_checkout_url_carries_plan_and_org():
    provider = StubBillingProvider(get_settings())
    session = asyncio.run(
        provider.create_checkout_session(
            organization_id="org-uuid", plan=Plan.PRO, customer_id=None, customer_email=None
        )
    )
    assert "plan=pro" in session.url
    assert "org=org-uuid" in session.url


def test_stub_parses_synthetic_checkout_event():
    provider = StubBillingProvider(get_settings())
    state = provider.parse_event_object(
        "stub.checkout.completed", {"organization_id": "abc", "plan": "agency"}
    )
    assert state is not None
    assert state.plan == Plan.AGENCY
    assert state.status == "active"
    assert state.stripe_customer_id == "cus_stub_abc"


def test_stripe_provider_parses_subscription_updated():
    settings = get_settings()
    object.__setattr__(settings, "stripe_price_pro", "price_pro_123")
    provider = StripeBillingProvider(settings)
    period_end = int(datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp())
    obj = {
        "id": "sub_1",
        "customer": "cus_1",
        "status": "active",
        "current_period_end": period_end,
        "items": {"data": [{"price": {"id": "price_pro_123"}}]},
    }
    state = provider.parse_event_object("customer.subscription.updated", obj)
    assert state.plan == Plan.PRO
    assert state.status == "active"
    assert state.stripe_subscription_id == "sub_1"
    assert state.current_period_end.year == 2026


def test_stripe_provider_deleted_event_is_canceled():
    provider = StripeBillingProvider(get_settings())
    state = provider.parse_event_object(
        "customer.subscription.deleted",
        {"id": "sub_1", "customer": "cus_1", "status": "active", "items": {"data": []}},
    )
    assert state.status == "canceled"
