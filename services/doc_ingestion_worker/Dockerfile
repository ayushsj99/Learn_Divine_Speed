FROM python:3.12-slim AS base
RUN pip install --no-cache-dir uv
WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY libs/shared /app/libs/shared
COPY services/doc_ingestion_worker /app/services/doc_ingestion_worker

RUN uv sync --frozen --package doc-ingestion-worker --no-dev

# One-shot batch job, not a long-running server — invoked via
# `docker compose run --rm doc_ingestion_worker python -m doc_ingestion_worker.run --framework <name>`
ENTRYPOINT ["uv", "run", "--package", "doc-ingestion-worker", "python", "-m", "doc_ingestion_worker.run"]
