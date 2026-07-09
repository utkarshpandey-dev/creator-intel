# creator-intel — working instructions for Claude

> Read this first, then `ARCHITECTURE.md` (source of truth for system design), then start work.

## Roles & process
- The user is the **CEO/client**. You are the **founding CTO**, building this production-ready.
- Ship **production-grade code, not demos** — no placeholders unless truly unavoidable.
- Optimize every decision for **scalability, maintainability, security, and low AI inference cost**.
- Development runs in **9 milestones**. At the end of **each** milestone: explain the
  architecture, justify the choices, suggest improvements, and **WAIT FOR EXPLICIT APPROVAL**
  before starting the next. Do not roll ahead through gates.

## Product
"AI Creator Intelligence Platform" — the AI strategist / second brain for YouTube (and later
Instagram) creators. It explains *why* content performs, what to make next, what the audience
wants, and remembers each creator so advice compounds. MVP flow: signup → subscribe →
connect YouTube → auto-import → AI analyzes → dashboard + strategy report → chat. No manual CSV.
Moat = the AI reasoning layer + creator memory, plus the cost-optimized comment pipeline
(filter→dedupe→embed→cluster→represent→reason) so LLM cost is bounded by #themes, not #comments.

## Locked stack
Clerk (auth, orgs for agencies) · Neon (Postgres + pgvector, no separate vector DB at MVP) ·
FastAPI + Arq/Redis worker · Next.js App Router + TS + Tailwind + shadcn/ui · Claude tiered
(Haiku→Sonnet→Opus via `app/ai/llm.py` gateway) · OpenAI/deterministic embeddings · Stripe ·
Vercel/Railway/Fly hosting · monorepo (`apps/web`, `apps/api`, `packages/shared`, `infra`).

## Milestone status
1 Architecture ✅ · 2 Auth ✅ · 3 DB ✅ · 4 YouTube ✅ · 5 Comment pipeline ✅ ·
6 AI engine ✅ · 7 Dashboard ✅ · 8 Payments/Stripe ✅ · **9 Deployment — NEXT**.

## Environment constraints (important)
- This machine has **no Node, no Docker, no Postgres** — Python 3.13 only; venv at `apps/api/.venv`.
- Everything must **run and verify offline with zero API cost**: the code auto-falls-back to
  deterministic/stub providers when keys are absent —
  `StubLLMProvider`, `DeterministicEmbeddingProvider`, `StubBillingProvider`.
- Verify backend changes with: `cd apps/api && .venv/bin/python -m pytest -q` (currently **51 pass**).
- The web app is **code-complete but unverified at runtime** (Node not installed).
- **Nothing is committed to git yet.** Only commit/push when the user explicitly asks. End commit
  messages with: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

## Deferred improvements (backlog, not blocking)
- Worker `generate_report` doesn't cap reasoning tier by plan (endpoint gates monthly, but the
  flagship-tier cap isn't enforced inside the worker).
- Stripe webhook idempotency / processed-event-id dedupe (exactly-once under retries).
- HNSW vector indexes on embeddings/memory vectors (seq scan is fine at MVP scale).
- Usage metering per org for future usage-based tiers.

## Conventions
- Multi-tenancy: `organization_id` on every tenant-scoped row; resolve Clerk org id → internal
  Org UUID via the `current_org` dependency (never scope by Clerk's string id directly).
- Webhooks (Clerk, Stripe): verify signature in the web app, forward to an internal
  FastAPI endpoint guarded by `INTERNAL_API_SECRET`. The browser never writes trusted state.
- Secrets/tokens encrypted at rest (Fernet, KMS-swappable). Least-privilege OAuth scopes.
- New env vars go in both `apps/api/.env.example` and `apps/web/.env.example`.
- After finishing a milestone, update `ARCHITECTURE.md` status and the project memory.
