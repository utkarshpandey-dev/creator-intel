# creator-intel API

FastAPI backend — auth (Milestone 2), database (Milestone 3), and the AI pipeline (later).

## Local setup

```bash
# 1. Dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Start local Postgres (pgvector) + Redis
docker compose -f ../../infra/docker/docker-compose.yml up -d

# 3. Configure env
cp .env.example .env    # fill in Clerk values; DATABASE_URL default matches docker

# 4. Apply migrations
alembic upgrade head

# 5. Run the API
uvicorn app.main:app --reload

# 6. Run the background worker (imports run here) in a second terminal
arq app.worker.settings.WorkerSettings
```

Interactive docs at http://localhost:8000/docs.

## Database

- Models: `app/models/` (tenant, channel, content, ai).
- Migrations: `alembic/` — create new ones with
  `alembic revision --autogenerate -m "message"`, apply with `alembic upgrade head`.
- Preview a migration as SQL without a database: `alembic upgrade head --sql`.
- All tenant data access goes through `app/repositories/` (org-scoped by construction).

## Tests

```bash
pytest
```
