FROM node:20-slim AS frontend-build

WORKDIR /app/playground
COPY playground/package.json playground/package-lock.json ./

RUN --mount=type=cache,target=/root/.npm \
    npm ci

COPY playground/ ./
RUN npm run build


FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y curl
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=/root/.cache/pypoetry \
    --mount=type=cache,target=/root/.cache/pip \
    poetry config virtualenvs.create false && poetry lock && poetry install --no-root --no-interaction --no-ansi --only main

COPY ./talkingdb_nel /app/talkingdb_nel
COPY --from=frontend-build /app/playground/dist /app/playground/dist

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 8092

CMD ["poetry", "run", "uvicorn", "talkingdb_nel.main:app", "--host", "0.0.0.0", "--port", "8092", "--workers", "1", "--loop", "uvloop", "--http", "httptools"]
