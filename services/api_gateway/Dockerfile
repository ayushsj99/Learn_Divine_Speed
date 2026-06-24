FROM python:3.12-slim AS base
RUN pip install --no-cache-dir uv
WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY libs/shared /app/libs/shared
COPY services/api_gateway /app/services/api_gateway

RUN uv sync --frozen --package api-gateway --no-dev

EXPOSE 8000
CMD ["uv", "run", "--package", "api-gateway", "uvicorn", "api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
