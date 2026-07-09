"""Applies verified Clerk webhook events to our Postgres identity mirror.

The web app has already verified the Svix signature; this maps each event to an idempotent
upsert/delete. Unknown events are ignored. Membership events may arrive before their org/
user is mirrored — we raise LookupError so the caller returns non-2xx and Clerk retries.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .repositories import sync

logger = logging.getLogger("clerk_sync")


async def apply_event(session: AsyncSession, event_type: str, data: dict[str, Any]) -> None:
    if event_type in ("user.created", "user.updated"):
        await sync.upsert_user(
            session,
            clerk_user_id=data["id"],
            email=_primary_email(data),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            image_url=data.get("image_url"),
        )

    elif event_type == "user.deleted":
        await sync.delete_user(session, clerk_user_id=data["id"])

    elif event_type in ("organization.created", "organization.updated"):
        await sync.upsert_organization(
            session,
            clerk_org_id=data["id"],
            name=data.get("name") or "Untitled workspace",
            slug=data.get("slug"),
        )

    elif event_type == "organization.deleted":
        await sync.delete_organization(session, clerk_org_id=data["id"])

    elif event_type == "organizationMembership.created":
        await sync.add_membership(
            session,
            clerk_org_id=_org_id(data),
            clerk_user_id=_user_id(data),
            role=data.get("role") or "member",
        )

    elif event_type == "organizationMembership.deleted":
        await sync.remove_membership(
            session, clerk_org_id=_org_id(data), clerk_user_id=_user_id(data)
        )

    else:
        logger.info("ignoring event type=%s", event_type)


def _primary_email(data: dict[str, Any]) -> str | None:
    primary_id = data.get("primary_email_address_id")
    for addr in data.get("email_addresses", []) or []:
        if addr.get("id") == primary_id:
            return addr.get("email_address")
    emails = data.get("email_addresses") or []
    return emails[0].get("email_address") if emails else None


def _org_id(data: dict[str, Any]) -> str:
    org_id = (data.get("organization") or {}).get("id")
    if not org_id:
        raise LookupError("membership event missing organization id")
    return org_id


def _user_id(data: dict[str, Any]) -> str:
    user_id = (data.get("public_user_data") or {}).get("user_id")
    if not user_id:
        raise LookupError("membership event missing user id")
    return user_id
