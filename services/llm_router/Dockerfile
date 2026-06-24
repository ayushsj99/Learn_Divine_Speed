FROM python:3.12-slim AS base
RUN pip install --no-cache-dir uv
WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY libs/shared /app/libs/shared
COPY services/llm_router /app/services/llm_router

RUN uv sync --frozen --package llm-router --no-dev

EXPOSE 8001
CMD ["uv", "run", "--package", "llm-router", "uvicorn", "llm_router.main:app", "--host", "0.0.0.0", "--port", "8001"]
