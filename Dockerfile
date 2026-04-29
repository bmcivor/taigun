FROM python:3.13-slim AS base

COPY --from=docker.io/astral/uv:0.11.8 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

FROM base AS test

COPY taigun/ ./taigun/
COPY tests/ ./tests/

RUN uv sync --frozen --group dev
