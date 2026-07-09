# Creator Intelligence Platform — Architecture (Milestone 1)

> Working name: `creator-intel`. The AI strategist for YouTube & Instagram creators.
> This document is the source of truth for system design. Update it as decisions change.

## Product thesis

Analytics tells creators *what* happened. We explain **why** it happened, **what to make
next**, and **what the audience actually wants** — and we *remember* each creator so our
advice compounds over time. The moat is the **AI reasoning layer** + **creator memory**,
not the dashboard.

Two architectural north stars:
1. **Inference cost per creator stays flat as data grows.** Reasoning cost is bounded by
   the number of *themes*, not the number of *comments*.
2. **Insights compound.** Month 3 is smarter than Month 1 for the same creator.

## Locked decisions (Milestone 1)

| Concern       | Decision                                             |
|---------------|------------------------------------------------------|
| Auth          | **Clerk** (orgs/roles for agencies)                  |
| Database      | **Neon** — serverless Postgres + `pgvector`          |
| Vector store  | **pgvector inside Postgres** (no separate vector DB at MVP) |
| Core API      | **FastAPI** (Python — ML/AI ecosystem)               |
| Frontend      | **Next.js App Router + TypeScript + Tailwind + shadcn/ui** |
| Jobs/Queue    | **Redis + Arq** (async ingest & AI pipeline)         |
| Reasoning LLM | **Claude, tiered**: Haiku → Sonnet → Opus by task    |
| Embeddings    | Cheapest capable model, cached by content hash       |
| Payments      | **Stripe** (Checkout + Billing + webhooks)           |
| Hosting       | Vercel (web) · Railway/Fly (api+worker) · Neon · Upstash (Redis) |
| Repo          | **Monorepo** (`apps/web`, `apps/api`, `packages/shared`) |

## System topology

```
Browser (Next.js) ──Clerk JWT──► Next.js BFF ──REST──► FastAPI ──► Postgres+pgvector
        ▲                                                  │
        └────────────── SSE / streaming chat ──────────────┘
                                                           │ enqueue
                                                           ▼
                                              Redis + Arq worker
                                              (ingest · comment pipeline ·
                                               report generation · scheduled refresh)
                                                           │
                          ┌────────────────┬───────────────┴───────────────┐
                          ▼                ▼                               ▼
                   YouTube Data API   Embedding model            Claude (tiered)
```

Next.js stays thin (auth, Stripe webhooks, serving UI, streaming proxy). All heavy
lifting lives in FastAPI + the worker.

## The AI cost-optimization pipeline (core IP)

Runs as an async job. Never in a request/response cycle.

1. **Cheap filter (no LLM):** spam/bot heuristics, emoji-only, links, <3 words, language
   detection. Drops ~40–60% of volume for free.
2. **Near-duplicate collapse (no LLM):** MinHash/SimHash; "great video!" ×3000 → 1 record
   with `weight=3000`.
3. **Embeddings (cheap, batched, cached by content hash):** never re-embed the same text.
4. **Clustering (no LLM):** HDBSCAN/k-means → ~40–80 theme clusters.
5. **Representative selection (no LLM):** per cluster → centroid + 2–3 exemplars + size +
   sentiment.
6. **Reasoning LLM (the ONLY expensive call):** input = cluster summaries, not raw
   comments → themes, requests, complaints, sentiment, strategy.
7. **Persist** structured insights + write to creator **memory**.

Effect: "50,000 comments → LLM" (impossible + costly) becomes "~80 cluster summaries →
LLM" (cents to dollars). Steps 1,2,4,5 use **zero** LLM tokens.

## Model tiering

- Filter/classify → deterministic code / tiny model.
- Embeddings → cheapest capable model, cached.
- Routine summaries / weekly reports → **Claude Haiku**.
- Deep strategy, "why viral", chat reasoning → **Claude Sonnet**.
- Flagship monthly strategy report → **Claude Opus** (only here).

All LLM calls go through a thin internal **AI gateway** interface so models are swappable
without touching business logic. Every insight stores the model + prompt version that
produced it.

## AI Memory (first-class subsystem)

- **Structured profile** (rows): niche, goals, subscriber history, past scores.
- **Episodic memory** (rows + pgvector): each report/recommendation/notable shift stored
  as a summarized, embedded memory record.
- **Retrieval at inference (RAG):** for new reports & chat, semantically retrieve only the
  *relevant* memories and inject those. This is what makes advice compound.

## Data model (first pass)

```
organizations            multi-tenant root (agencies manage many creators)
  users                  Clerk-synced; role owner/member
  subscriptions          Stripe: plan, status, limits
channels                 a connected YouTube channel (belongs to org)
  oauth_tokens           encrypted at rest; refresh tokens
  videos                 metadata + stats snapshots over time
  comments               raw → filtered → weighted
  comment_clusters
  embeddings             pgvector (comments + memory records)
  insights               structured AI output (scores, themes, requests…)
  reports                weekly/monthly generated docs
  memory_records         episodic AI memory, embedded
```

**Multi-tenancy from day one:** `organization_id` on every tenant-scoped row, enforced at
the data-access layer.

## Security non-negotiables

- YouTube OAuth refresh tokens **encrypted at rest** (envelope encryption); never logged.
- Tenant isolation enforced on every query by `organization_id`.
- Stripe webhooks signature-verified; subscription state gates features.
- Least-privilege YouTube OAuth scopes (read-only analytics).
- Rate limiting around YouTube API quota (finite, per-project).
- PII minimization + deletion/GDPR path from the start.

## Scalability path (when, not now)

- pgvector → dedicated vector DB (Qdrant/Pinecone) when vector volume demands it.
- Single worker pool → per-queue workers (ingest vs. reasoning) for isolation.
- Neon → RDS/Aurora if we outgrow serverless limits.
- Source connectors are pluggable → Instagram added without rewriting the pipeline.

## Milestones

1. **Architecture** ✅ (this document)
2. **Authentication (Clerk)** ✅ — middleware, JWT verification, org scoping, webhook sync
3. **Database (Neon + schema + migrations)** ✅ — SQLAlchemy 2.0 async, pgvector, Alembic
4. **YouTube integration (OAuth + ingest)** ✅ — OAuth, encrypted tokens, Arq import worker
5. **Comment processing pipeline** ✅ — filter→dedupe→embed(cached)→cluster→represent
6. **AI engine (gateway, tiering, memory, reports)** ✅ — tiered Claude, scoring, RAG memory, chat
7. **Dashboard** ✅ — score gauges, audience themes, reports, video table, streaming chat
8. **Payments (Stripe)** ✅ — plan catalog + feature limits, Checkout, customer portal,
   signature-verified webhooks syncing `subscriptions`, plan-based gating (channel cap,
   AI chat, monthly flagship report). Offline stub provider runs the whole flow with no
   Stripe account.
9. **Deployment** ✅ — containerized API+worker (one image, two Fly process groups),
   `alembic upgrade head` as Fly `release_command`, Vercel for web with security headers,
   fail-fast production config guard (`Settings.validate_for_deploy`), GitHub Actions CI
   (API lint+tests, web typecheck+build), full-stack local docker-compose parity, and a
   deployment runbook (`DEPLOYMENT.md`). See that file for hosting map and operations.

Gate after each: explain, justify, suggest improvements, wait for approval.
