from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, loaded from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Deployment environment. "production" turns on fail-fast config validation
    # (see validate_for_deploy) so we never ship with default secrets or plaintext DB.
    app_env: str = "development"

    # Clerk. The issuer is your Clerk Frontend API URL, e.g.
    # https://your-app.clerk.accounts.dev  (or your production domain).
    # JWKS is derived from it unless overridden.
    clerk_issuer: str = "https://example.clerk.accounts.dev"
    clerk_jwks_url: str | None = None
    # Optional: restrict accepted authorized parties (frontend origins).
    clerk_authorized_parties: list[str] = []

    # Shared secret protecting internal endpoints (must match the web app).
    internal_api_secret: str = "change-me-to-a-long-random-string"

    # Database. Use the async driver. For Neon, take the pooled connection string and
    # convert scheme to postgresql+asyncpg://  (drop ?sslmode=..., ssl is handled below).
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/creator_intel"
    db_echo: bool = False
    db_require_ssl: bool = False  # set True for Neon / any managed Postgres

    # Embedding vector dimension. Must match the embedding model chosen in Milestone 6.
    # Default targets a small, cheap 1536-dim model; changing it later requires a migration.
    embedding_dim: int = 1536

    # --- Milestone 4: YouTube / Google OAuth ---
    google_client_id: str = ""
    google_client_secret: str = ""
    # Must exactly match an authorized redirect URI in the Google Cloud console.
    google_redirect_uri: str = "http://localhost:8000/youtube/oauth/callback"
    youtube_scopes: list[str] = [
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/yt-analytics.readonly",
    ]
    # Where to send the user back in the web app after a connect completes.
    web_app_url: str = "http://localhost:3000"
    # Signed OAuth-state lifetime (seconds). Short — it only spans the redirect round-trip.
    oauth_state_ttl: int = 600

    # Fernet key for encrypting OAuth tokens at rest. Generate with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # In production this is a KMS-wrapped data key; here it's an app-managed secret.
    token_encryption_key: str = ""

    # Redis (Arq worker + queue).
    redis_url: str = "redis://localhost:6379"

    # Import guardrails to respect YouTube quota.
    import_max_videos: int = 200
    import_max_comments_per_video: int = 500

    # --- Milestone 5: comment pipeline ---
    # Embedding provider: "openai" (hosted) or "deterministic" (offline/dev, no API cost).
    # Falls back to deterministic automatically when no API key is configured.
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    embedding_batch_size: int = 128

    # Filtering / clustering knobs.
    min_comment_words: int = 3
    max_clusters: int = 80
    min_comments_to_cluster: int = 5

    # --- Milestone 6: AI engine (tiered Claude) ---
    # Falls back to a deterministic offline stub when no API key is configured, so the
    # engine (scoring, reports, memory, chat) runs end-to-end with zero API cost in dev.
    anthropic_api_key: str = ""
    # Model tiering by task cost/complexity (see ARCHITECTURE.md § Model tiering).
    model_cheap: str = "claude-haiku-4-5"   # labels, quick summaries
    model_standard: str = "claude-sonnet-5"  # weekly reports
    model_flagship: str = "claude-opus-4-8"  # monthly strategy + chat reasoning
    # Bump when a prompt template changes, so stored insights are traceable.
    prompt_version: str = "v1"
    # How many memory records to retrieve for RAG context.
    memory_top_k: int = 6

    # --- Milestone 8: payments (Stripe) ---
    # Falls back to an offline stub when no secret key is configured, so the subscribe
    # flow (checkout redirect, portal, webhook sync) runs end-to-end with zero Stripe
    # account in dev/preview. Never charge or hit Stripe without a real key.
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    # Signature secret for the webhook endpoint (verified in the web app before forwarding).
    stripe_webhook_secret: str = ""
    # Price ids from the Stripe dashboard, one per paid plan. Empty in dev → stub checkout.
    stripe_price_pro: str = ""
    stripe_price_agency: str = ""
    # Where Stripe Checkout returns the user after success/cancel.
    billing_success_url: str = "http://localhost:3000/dashboard/billing?checkout=success"
    billing_cancel_url: str = "http://localhost:3000/dashboard/billing?checkout=cancel"

    # CORS: the web app origin(s) allowed to call this API from the browser.
    cors_origins: list[str] = ["http://localhost:3000"]

    # Sentinel defaults that are safe for offline dev but must never reach production.
    _DEFAULT_INTERNAL_SECRET = "change-me-to-a-long-random-string"
    _EXAMPLE_CLERK_ISSUER = "https://example.clerk.accounts.dev"

    @property
    def jwks_url(self) -> str:
        return self.clerk_jwks_url or f"{self.clerk_issuer.rstrip('/')}/.well-known/jwks.json"

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in {"production", "prod"}

    def deploy_config_errors(self) -> list[str]:
        """Return production misconfigurations, empty if safe to deploy.

        These are hard footguns — a default shared secret, a plaintext DB connection, or a
        missing token-encryption key would each be a security incident in production, so we
        fail fast at startup rather than serve traffic in a broken trust posture.
        """
        errors: list[str] = []
        if not self.is_production:
            return errors

        if self.internal_api_secret == self._DEFAULT_INTERNAL_SECRET:
            errors.append("INTERNAL_API_SECRET is still the default placeholder.")
        elif len(self.internal_api_secret) < 24:
            errors.append("INTERNAL_API_SECRET must be at least 24 characters.")

        if not self.token_encryption_key:
            errors.append("TOKEN_ENCRYPTION_KEY is required to encrypt OAuth tokens at rest.")

        if self.clerk_issuer == self._EXAMPLE_CLERK_ISSUER:
            errors.append("CLERK_ISSUER is still the example value.")

        if not self.db_require_ssl:
            errors.append("DB_REQUIRE_SSL must be true for a managed Postgres (Neon).")

        if any("localhost" in origin or "127.0.0.1" in origin for origin in self.cors_origins):
            errors.append("CORS_ORIGINS must not include localhost in production.")

        return errors

    def validate_for_deploy(self) -> None:
        """Raise if running in production with an unsafe configuration."""
        errors = self.deploy_config_errors()
        if errors:
            joined = "\n  - ".join(errors)
            raise RuntimeError(
                "Refusing to start: unsafe production configuration:\n  - " + joined
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
