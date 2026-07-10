# Creator Intel

**The AI operating system for YouTube & Instagram creators.** It explains *why* your content
performs, *what* your audience actually wants, and *what* to make next — then remembers your
channel so the advice compounds over time.

> 🌐 **Live:** [creator-intel-utk4.vercel.app](https://creator-intel-utk4.vercel.app)
> · API: [creator-intel-api.fly.dev](https://creator-intel-api.fly.dev/health)
> · Design & rationale: [`ARCHITECTURE.md`](./ARCHITECTURE.md) · Ops: [`DEPLOYMENT.md`](./DEPLOYMENT.md)

---

## What it does

- **Why it performed** — reasoned explanations for each video (hook, topic, timing, audience fit), not just view counts.
- **Audience intelligence** — tens of thousands of comments distilled into ranked themes, requests, and complaints.
- **Next-move engine** — concrete, prioritized content ideas grounded in your own data.
- **Compounding memory** — every report and shift is remembered via pgvector RAG, so month three is smarter than month one.
- **Cost-bounded AI** — a `filter → dedupe → embed → cluster → represent → reason` pipeline keeps LLM cost tied to the number of *themes*, not the number of *comments*.
- **AI strategist chat** — ask anything about your channel; answers stream from your real numbers and history.

## Stack

Next.js (App Router · TS · Tailwind) · FastAPI (Python) · Neon (Postgres + `pgvector`) ·
Redis + Arq worker · Clerk (auth + orgs) · Stripe (billing) · Claude, tiered (Haiku → Sonnet → Opus).

## Live infrastructure

| Layer | Host | Status |
|---|---|---|
| Web (Next.js) | Vercel | 🟢 live |
| API + worker | Fly.io (2 process groups, 1 image) | 🟢 live |
| Postgres + pgvector | Neon | 🟢 live |
| Redis queue | Upstash | 🟢 live |
| Auth + organizations | Clerk (+ verified webhook) | 🟢 live |
| Billing | Stripe (test mode, verified webhook) | 🟢 live |
| YouTube ingest | Google OAuth | 🟡 pending credentials |
| Reasoning / embeddings | Claude / OpenAI | 🟡 deterministic stubs until keys set |

## Monorepo layout

```
apps/
  web/          Next.js — UI, Clerk/Stripe webhook receivers, streaming chat proxy
  api/
    app/        FastAPI — auth, YouTube ingest, comment pipeline, AI engine, billing
    worker/     Arq background jobs (import · pipeline · report generation)
    alembic/    Database migrations (SQLAlchemy 2.0 async)
    tests/      Offline test suite (60 passing, zero API cost)
infra/
  docker/       Local dev + full-stack docker-compose (Postgres+pgvector, Redis, api, worker)
.github/
  workflows/    CI (API lint+tests, web typecheck+build) and guarded Fly deploy
```

## Local development

The backend runs fully offline with **zero API cost** — it auto-falls back to deterministic
and stub providers (`StubLLMProvider`, `DeterministicEmbeddingProvider`, `StubBillingProvider`)
whenever real keys are absent.

```bash
# 1. Infra (Postgres + Redis)
docker compose -f infra/docker/docker-compose.yml up -d postgres redis

# 2. API
cd apps/api
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload

# 3. Worker (separate shell)
.venv/bin/arq app.worker.settings.WorkerSettings

# 4. Web
cd apps/web && npm install && cp .env.example .env.local && npm run dev
```

Verify backend changes:

```bash
cd apps/api && .venv/bin/python -m pytest -q     # 60 passing
```

## Deployment

Production runs on Fly (API + worker) and Vercel (web), with Neon and Upstash as managed data
services. Migrations apply automatically as a Fly release step. Full runbook — provisioning,
secrets, webhook wiring, smoke tests, and rollback — in [`DEPLOYMENT.md`](./DEPLOYMENT.md).

## Security

Multi-tenant isolation by `organization_id` on every row · OAuth tokens encrypted at rest
(Fernet) · signature-verified Clerk & Stripe webhooks forwarded server-to-server behind an
internal shared secret · least-privilege read-only YouTube scopes · fail-fast production
config validation that refuses to boot on default secrets or a plaintext database.
