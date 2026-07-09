# creator-intel

The AI strategist for YouTube & Instagram creators — explains *why* content performs,
*what* to make next, and *what* the audience actually wants. See
[`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full system design.

## Monorepo layout

```
apps/
  web/        Next.js (App Router, TS, Tailwind, shadcn/ui) — UI, auth, Stripe webhooks
  api/        FastAPI — core API, YouTube ingest, AI orchestration, chat
    app/      HTTP API
    worker/   Redis/Arq background jobs (ingest & AI pipeline)
packages/
  shared/     Shared contracts / generated TS client from the API's OpenAPI schema
infra/
  migrations/ Database migrations
  docker/     Local dev containers (Postgres+pgvector, Redis)
```

## Stack

Next.js · TypeScript · Tailwind · FastAPI (Python) · Neon (Postgres + pgvector) ·
Redis + Arq · Clerk (auth) · Stripe (billing) · Claude (tiered reasoning).

## Status

Milestones 1–8 complete. Milestone 9 (Deployment) implemented, pending approval — see
[`DEPLOYMENT.md`](./DEPLOYMENT.md) for the production runbook (Fly + Vercel + Neon + Upstash).
