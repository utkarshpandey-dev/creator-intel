"""Milestone 9: production configuration guardrails.

These assert the fail-fast validator (Settings.validate_for_deploy) catches the deployment
footguns — default shared secret, plaintext DB, missing token key — before serving traffic.
All offline, zero cost.
"""

import pytest

from app.config import Settings

# A configuration that would be safe to run in production.
SAFE = dict(
    app_env="production",
    internal_api_secret="a-real-long-random-internal-secret-value",
    token_encryption_key="Zk1n0m3rANDOMfernetKEYplaceholdervalue123456=",
    clerk_issuer="https://clerk.creatorintel.app",
    db_require_ssl=True,
    cors_origins=["https://app.creatorintel.app"],
)


def test_development_env_skips_validation():
    # Defaults are placeholders; that's fine in development.
    s = Settings(app_env="development")
    assert s.deploy_config_errors() == []
    s.validate_for_deploy()  # must not raise


def test_production_safe_config_passes():
    s = Settings(**SAFE)
    assert s.is_production is True
    assert s.deploy_config_errors() == []
    s.validate_for_deploy()


def test_production_rejects_default_internal_secret():
    s = Settings(**{**SAFE, "internal_api_secret": "change-me-to-a-long-random-string"})
    errors = s.deploy_config_errors()
    assert any("INTERNAL_API_SECRET" in e for e in errors)
    with pytest.raises(RuntimeError):
        s.validate_for_deploy()


def test_production_rejects_short_internal_secret():
    s = Settings(**{**SAFE, "internal_api_secret": "too-short"})
    assert any("at least 24" in e for e in s.deploy_config_errors())


def test_production_requires_token_encryption_key():
    s = Settings(**{**SAFE, "token_encryption_key": ""})
    assert any("TOKEN_ENCRYPTION_KEY" in e for e in s.deploy_config_errors())


def test_production_requires_ssl():
    s = Settings(**{**SAFE, "db_require_ssl": False})
    assert any("DB_REQUIRE_SSL" in e for e in s.deploy_config_errors())


def test_production_rejects_example_clerk_issuer():
    s = Settings(**{**SAFE, "clerk_issuer": "https://example.clerk.accounts.dev"})
    assert any("CLERK_ISSUER" in e for e in s.deploy_config_errors())


def test_production_rejects_localhost_cors():
    s = Settings(**{**SAFE, "cors_origins": ["http://localhost:3000"]})
    assert any("CORS_ORIGINS" in e for e in s.deploy_config_errors())


def test_all_errors_are_collected_not_just_first():
    s = Settings(app_env="production")  # everything at defaults
    errors = s.deploy_config_errors()
    # default secret, missing token key, example issuer, no ssl, localhost cors
    assert len(errors) >= 4
