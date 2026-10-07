# Backend image for the API and ingest CLI.
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_FROZEN=1

# Install dependencies first (cached unless the lockfile changes).
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-dev --no-install-project

# Copy and install the application.
COPY app ./app
RUN uv sync --no-dev

EXPOSE 8000

# Default: serve the API. The ingest service overrides this command.
CMD ["uv", "run", "uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
