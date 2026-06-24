FROM python:3.12-slim AS base
RUN pip install --no-cache-dir uv
WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY libs/shared /app/libs/shared
COPY services/sandbox /app/services/sandbox

RUN uv sync --frozen --package sandbox --no-dev

EXPOSE 8004
CMD ["uv", "run", "--package", "sandbox", "uvicorn", "sandbox.main:app", "--host", "0.0.0.0", "--port", "8004"]
