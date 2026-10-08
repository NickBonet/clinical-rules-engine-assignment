# Clinical Rules Engine

A simplified clinical rules engine for a population-health platform: it evaluates
patient eligibility and risk tier per program, derives clinical needs, generates
actionable tasks, and serves role-scoped worklists via an API and a lightweight
frontend.

See [ARCHITECTURE.md](ARCHITECTURE.md) for
the architecture, data model, and design decisions.

## Layout

```
data/        provided CSVs for the assignment
backend/     FastAPI app, rules engine, task generation, pipeline (uv-managed)
  app/domain/      pure domain types (facts, needs, tasks)
  app/engine/      pure evaluation core: programs, rules engine, task generation
  app/repository/  storage behind a Protocol (one SQLAlchemy repo: SQLite + Postgres)
  app/pipeline/    CSV ingest, as-of resolution, patient evaluation orchestration
  app/api/         app setup, routers, dependencies, typed response schemas
frontend/    React + TypeScript (Vite) UI
  src/api/         typed API client and shared types
  src/hooks/       patient/task data loading for the given views
  src/components/  filters, reference date, patient and task tables
docker-compose.yml   Used to stand up the whole stack (API, frontend, Postgres, initial ingest)
```

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python) and Python 3.11+
- Node 24+ (frontend uses Vite; npm is fine — no yarn/pnpm required)
- Docker with the Compose plugin (can stand up the stack with the provided Compose file)

## Run it

**1. Backend**

```bash
cd backend
uv sync
uv run ingest                 # optional in-memory evaluation; prints a summary
uv run ingest --as-of 2026-04-07   # override the reference date
uv run uvicorn app.api.main:app --reload   # serve the API on :8000
```

The local API loads and evaluates CSVs into in-memory SQLite at startup; CLI ingest
is optional and separate. Set `APP_AS_OF` when starting the API to override its date.
See the [backend README](backend/README.md#api-reference) for endpoints, filters,
and Swagger documentation.

**2. Frontend**

```bash
cd frontend                   # from the repository root, in another terminal
npm install
npm run dev                   # http://localhost:5173, proxies /api -> :8000
```

**3. Postgres (persistent backend)**

```bash
docker compose up --build -d                      # from the repository root
```

Starts Postgres, initial ingestion, API, and frontend. Open the frontend at
`http://localhost:5173`; the API is on port 8000 and Postgres on 5432. Stop local
servers using these ports first. Deployment details are in the architecture summary.

## Re-ingest Postgres With Docker

With the database running, execute from the repository root:

```bash
docker compose stop backend
docker compose build ingest backend              # include current rule code
docker compose run --rm --no-deps ingest uv run ingest --backend postgres --as-of 2026-04-07
# Only after ingestion succeeds:
docker compose up -d --no-deps backend
curl http://localhost:8000/health
```

Choose the desired date; omit `--as-of` for the configured/default date. Keep the
API stopped if ingestion fails. Restarting it reloads the stored date; refresh the
frontend afterward. No volume reset is needed. Persistence caveats are in the
architecture summary.

## Checks

```bash
# From the repository root:
uv run --project backend ruff check backend/app
npm --prefix frontend run build
```

The frontend build includes TypeScript checking. The test suite was removed for
this assignment.

## Key assumptions

- **Reference ("as-of") date** defaults to `max(lab result_date)` = 2026-04-07,
  overridable via `--as-of` / `APP_AS_OF`. Using today's date instead changes
  A1C windows and which encounters count as upcoming.
- **Diagnosis dates** must be on or before `as_of` to affect eligibility or risk.
- **"Within last 6 months" = 180 days**, inclusive.
- **Most recent A1C** = latest A1C within the window; ties broken by higher value.
  Future lab results are excluded; datasets without labs require an explicit date.
- **Referral tasks apply to specialists only**; a patient with no PCP encounter
  history generates no Primary Care Wellness task.
- **"Upcoming encounter → no task"** is applied to all specialties, including PCP.
- **Validation** rejects missing/blank visit specialties and unknown wellness risk tiers.
