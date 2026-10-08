# Backend — Clinical Rules Engine

FastAPI service, pure rules engine, task generation, and the CSV pipeline.
See the [root README](../README.md) for how to run it and the
[architecture summary](../assignment_architecture_summary.md) for design.

```bash
uv sync
uv run ingest            # optional in-memory evaluation; prints a summary
uv run uvicorn app.api.main:app --reload
```

Run these commands from `backend/`. SQLite API startup loads and evaluates CSVs
in memory, independently of any CLI run. For CLI options, run `uv run ingest --help`;
supported flags are `--backend`, `--as-of`, and `--data-dir`. Settings use the
`APP_` environment prefix or `.env`. To override a local SQLite API's date:

```bash
APP_AS_OF=2025-01-01 uv run uvicorn app.api.main:app --reload
```

## Postgres With Docker

Postgres ingestion persists facts and derived results; the API reads them without
reevaluation. See the [root README](../README.md#re-ingest-postgres-with-docker)
for Docker startup and re-ingestion commands, including rebuilding rule code,
stopping the API during ingestion, and restarting it to reload the saved date.
Changing `APP_AS_OF` on the API alone does not reevaluate stored results.

## API Reference

| Endpoint | Response | Query filters |
|---|---|---|
| `GET /health` | Status and evaluation date | None |
| `GET /patients` | Patients with enrollments, risk tiers, and visible tasks | `role`, `specialty`, `task_type` |
| `GET /tasks` | Visible tasks | `role`, `specialty`, `task_type` |
| `GET /specialties` | Sorted distinct specialties with visible tasks | `role` |

`role` defaults to `clinical`. `scheduler` sees scheduling tasks only; `clinical`
sees scheduling and referrals. This is a query filter, not authentication or
authorization. `specialty` matches the exact specialty name; `task_type` accepts
`scheduling` or `referral`. Invalid role/task-type values return HTTP 422.

For `/patients`, specialty/task-type filters return only patients with a matching
role-visible task and include only matching tasks. Without these filters, patients
with enrollments or visible tasks are included; enrolled patients may have an empty
task list. Enrollments are not filtered. All list endpoints are unpaginated.

`/specialties` is independent of the selected specialty/task-type filter, so the
dropdown remains complete for the role.

Example: `/tasks?role=clinical&specialty=Endocrinology&task_type=referral`.

Swagger is at `http://localhost:8000/docs` locally; OpenAPI is at `/openapi.json`.
With Docker, open `http://localhost:5173/api/docs` through the frontend proxy.

## API Structure

- `app/api/main.py`: application setup, middleware, lifespan, and router registration.
- `app/api/routes/`: separate routers for health, patients, tasks, and specialties.
- `app/api/dependencies.py`: request-scoped repository access, role visibility, and query annotations.
- `app/api/schemas.py`: typed response models used for validation and OpenAPI documentation.

Response models provide validation and named Swagger schemas. The frontend defaults
to scheduler and uses `/patients` for both views, flattening its tasks for the task
view. It loads `/specialties` separately and clears filters when switching roles.

## Configuration

Settings are read from `APP_` environment variables or `.env` in the working directory.

| Variable | Purpose |
|---|---|
| `APP_BACKEND` | `sqlite` (default) or `postgres` |
| `APP_DATABASE_URL` | Postgres connection URL; localhost locally, `db` in Compose |
| `APP_DATA_DIR` | CSV directory; defaults to repository `data/`, `/data` in Compose |
| `APP_AS_OF` | Evaluation date; defaults to latest lab result date during ingest |
| `APP_ROOT_PATH` | External proxy prefix; empty locally, `/api` in Compose |

Tables use `create_all`; ingestion does not migrate existing database schemas.

## Engine Behavior

- Eligibility and risk use an explicit `as_of`; future diagnoses are ignored.
- A1C risk uses the latest result in the inclusive 180-day window, excluding future labs.
- Upcoming encounters suppress tasks; past visits are overdue only after their cadence.
- No specialist history produces a referral; no PCP history produces no task.
- Visit needs reject missing/blank specialties; wellness rejects unknown risk tiers.

## Checks

```bash
uv run ruff check app
```

The test suite was removed for this assignment.
