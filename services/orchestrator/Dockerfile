FROM python:3.12-slim AS base
RUN pip install --no-cache-dir uv
WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY libs/shared /app/libs/shared
COPY services/orchestrator /app/services/orchestrator
COPY migrations /app/migrations

RUN uv sync --frozen --package orchestrator --no-dev

EXPOSE 8002
CMD ["uv", "run", "--package", "orchestrator", "uvicorn", "orchestrator.main:app", "--host", "0.0.0.0", "--port", "8002"]
