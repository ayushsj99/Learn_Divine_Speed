FROM python:3.12-slim AS base
RUN pip install --no-cache-dir uv
WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY libs/shared /app/libs/shared
COPY services/retrieval /app/services/retrieval

RUN uv sync --frozen --package retrieval --no-dev

EXPOSE 8003
CMD ["uv", "run", "--package", "retrieval", "uvicorn", "retrieval.main:app", "--host", "0.0.0.0", "--port", "8003"]
