# Deployment runbook (Milestone 9)

Production topology, provisioning steps, and operations for `creator-intel`. This is the
source of truth for *how the system is deployed*; `ARCHITECTURE.md` covers *why*.

## Hosting map

| Component            | Host        | What runs                                        |
|----------------------|-------------|--------------------------------------------------|
| Web (Next.js)        | **Vercel**  | UI, Clerk/Stripe webhook receivers, BFF proxy    |
| API (FastAPI)        | **Fly.io**  | REST API — process group `app` (uvicorn)         |
| Worker (Arq)         | **Fly.io**  | Background jobs — process group `worker`          |
| Postgres + pgvector  | **Neon**    | Primary datastore + vector store                 |
| Redis                | **Upstash** | Arq queue                                         |

The API and worker share **one Fly app and one Docker image** (`apps/api/Dockerfile`);
they differ only by start command (see `apps/api/fly.toml` `[processes]`). Migrations run
as Fly's `release_command` (`alembic upgrade head`) before each rollout takes traffic.

```
Browser ──► Vercel (Next.js) ──REST──► Fly app process ──► Neon (Postgres+pgvector)
                                              │ enqueue
                                              ▼
                                      Upstash (Redis) ──► Fly worker process
```

## 0. Prerequisites

Accounts: Vercel, Fly.io (`flyctl`), Neon, Upstash, Clerk, Stripe, Google Cloud.
Install the Fly CLI: `curl -L https://fly.io/install.sh | sh`.

## 1. Provision managed data services

**Neon** — create a project (region near Fly's `iad`, e.g. AWS us-east). Enable the
`vector` extension is automatic on first migration (the initial migration creates it).
Copy the **pooled** connection string and convert it for asyncpg:

- scheme `postgresql://` → `postgresql+asyncpg://`
- drop any `?sslmode=...` query param (SSL is passed via `DB_REQUIRE_SSL=true`)

**Upstash** — create a Redis database, copy the `rediss://` URL (TLS). Arq reads it from
`REDIS_URL`.

## 2. Generate app secrets

```bash
# Fernet key for OAuth-token encryption at rest
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Shared secret between web app and API internal endpoints (must be identical on both)
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 3. Provision third-party auth/billing/data APIs

- **Clerk** — create a production instance. Note the Frontend API URL (`CLERK_ISSUER`),
  publishable + secret keys, and create a **webhook** (§6).
- **Stripe** — create products/prices for Pro and Agency; note the price ids and the
  webhook signing secret (§6).
- **Google Cloud** — OAuth 2.0 Web client. Authorized redirect URI must exactly match
  `GOOGLE_REDIRECT_URI` = `https://<api-host>/youtube/oauth/callback`. Scopes are
  read-only (`youtube.readonly`, `yt-analytics.readonly`).

## 4. Deploy the API + worker (Fly)

```bash
cd apps/api
fly launch --no-deploy            # creates the app from fly.toml (name: creator-intel-api)
```

Set secrets (never commit these — Fly injects them as env):

```bash
fly secrets set \
  APP_ENV=production \
  DATABASE_URL="postgresql+asyncpg://USER:PW@ep-xxx.aws.neon.tech/creator_intel" \
  DB_REQUIRE_SSL=true \
  REDIS_URL="rediss://:PW@xxx.upstash.io:6379" \
  INTERNAL_API_SECRET="<from step 2>" \
  TOKEN_ENCRYPTION_KEY="<from step 2>" \
  CLERK_ISSUER="https://clerk.yourdomain.com" \
  CORS_ORIGINS='["https://app.yourdomain.com"]' \
  GOOGLE_CLIENT_ID="..." GOOGLE_CLIENT_SECRET="..." \
  GOOGLE_REDIRECT_URI="https://creator-intel-api.fly.dev/youtube/oauth/callback" \
  WEB_APP_URL="https://app.yourdomain.com" \
  OPENAI_API_KEY="..." \
  ANTHROPIC_API_KEY="..." \
  STRIPE_SECRET_KEY="sk_live_..." \
  STRIPE_PRICE_PRO="price_..." STRIPE_PRICE_AGENCY="price_..." \
  BILLING_SUCCESS_URL="https://app.yourdomain.com/dashboard/billing?checkout=success" \
  BILLING_CANCEL_URL="https://app.yourdomain.com/dashboard/billing?checkout=cancel"

fly deploy                        # builds image, runs `alembic upgrade head`, rolls out
```

> **Fail-fast guard:** with `APP_ENV=production`, both processes refuse to start if
> `INTERNAL_API_SECRET` is the default, `TOKEN_ENCRYPTION_KEY` is empty, `DB_REQUIRE_SSL`
> is false, `CLERK_ISSUER` is the example, or `CORS_ORIGINS` contains localhost. A failed
> `fly deploy` release step here means one of these is wrong — fix the secret and redeploy.

Scale the worker separately from the API:

```bash
fly scale count app=2 worker=1
```

**Automated deploys (optional):** `.github/workflows/deploy.yml` runs `flyctl deploy` on
pushes to `main`. It's dormant until you opt in — set repo **variable** `DEPLOY_ENABLED=true`
and **secret** `FLY_API_TOKEN` (`fly tokens create deploy`). Until then, deploy manually with
`fly deploy` as above.

## 5. Deploy the web (Vercel)

- Import the repo; set **Root Directory** = `apps/web` (monorepo). Framework auto-detects
  Next.js; `apps/web/vercel.json` pins the build.
- Set environment variables (Production scope) from `apps/web/.env.example`:
  `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `CLERK_WEBHOOK_SECRET`,
  `API_BASE_URL` = `https://creator-intel-api.fly.dev`,
  `INTERNAL_API_SECRET` (same value as the API),
  `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`.
- Deploy. Note the production URL and set your custom domain (`app.yourdomain.com`).

## 6. Wire webhooks & redirect URIs (after both are live)

- **Clerk webhook** → `https://app.yourdomain.com/api/webhooks/clerk`
  (events: `user.*`, `organization.*`, `organizationMembership.*`). Signature is verified
  in the web app, then forwarded to the API's `/internal/clerk/sync` with the shared secret.
- **Stripe webhook** → `https://app.yourdomain.com/api/webhooks/stripe`
  (events: `checkout.session.completed`, `customer.subscription.*`). Same verify-then-forward.
- **Google OAuth** → confirm the redirect URI matches `GOOGLE_REDIRECT_URI` exactly.

The browser never writes trusted state: webhooks are signature-verified at the Vercel edge,
then forwarded server-to-server to the API guarded by `INTERNAL_API_SECRET`.

## 7. Post-deploy smoke test

```bash
curl -fsS https://creator-intel-api.fly.dev/health        # {"status":"ok"}
curl -fsS https://creator-intel-api.fly.dev/health/db      # {"status":"ok","db":"reachable"}
```

Then, in the browser: sign up → subscribe (Stripe test card) → connect YouTube → confirm
an import job runs (`fly logs -a creator-intel-api --instance <worker>`) → dashboard renders
→ chat streams. This is the full MVP flow from `CLAUDE.md`.

## 8. Migrations

Applied automatically by Fly's `release_command` on every deploy. To run manually:

```bash
fly ssh console -a creator-intel-api -C "alembic upgrade head"
```

New migration during development: `alembic revision --autogenerate -m "..."`, review the
generated file, commit — it ships on the next deploy.

## 9. Rollback

- **App/worker:** `fly releases -a creator-intel-api` then `fly deploy --image <prior>`
  (or `fly releases rollback`). Note: a rollback does **not** reverse a migration — write
  migrations to be backward-compatible (expand/contract), never destructive in one step.
- **Web:** promote the previous deployment from the Vercel dashboard (instant).

## 10. Operations

| Task                | Command                                                     |
|---------------------|------------------------------------------------------------|
| API/worker logs     | `fly logs -a creator-intel-api`                            |
| Live status         | `fly status -a creator-intel-api`                         |
| Shell into a VM     | `fly ssh console -a creator-intel-api`                     |
| Scale               | `fly scale count app=N worker=M`                          |
| Rotate a secret     | `fly secrets set KEY=... ` (triggers a rolling restart)   |
| Web logs            | Vercel dashboard → Deployment → Functions/Runtime logs    |

### Known follow-ups (see CLAUDE.md § Deferred improvements)
Worker reasoning-tier cap by plan, Stripe webhook idempotency, HNSW vector indexes, and
per-org usage metering are tracked backlog — not blockers for this deploy.
