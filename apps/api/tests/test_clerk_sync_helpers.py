"""Unit tests for pure Clerk-event parsing helpers (no DB required)."""

import pytest

from app.clerk_sync import _org_id, _primary_email, _user_id


def test_primary_email_prefers_primary_address():
    data = {
        "primary_email_address_id": "idb",
        "email_addresses": [
            {"id": "ida", "email_address": "a@example.com"},
            {"id": "idb", "email_address": "b@example.com"},
        ],
    }
    assert _primary_email(data) == "b@example.com"


def test_primary_email_falls_back_to_first():
    data = {"email_addresses": [{"id": "ida", "email_address": "a@example.com"}]}
    assert _primary_email(data) == "a@example.com"


def test_primary_email_none_when_absent():
    assert _primary_email({}) is None


def test_org_and_user_ids_extracted():
    data = {"organization": {"id": "org_1"}, "public_user_data": {"user_id": "user_1"}}
    assert _org_id(data) == "org_1"
    assert _user_id(data) == "user_1"


def test_missing_membership_ids_raise_lookup_error():
    with pytest.raises(LookupError):
        _org_id({})
    with pytest.raises(LookupError):
        _user_id({})
