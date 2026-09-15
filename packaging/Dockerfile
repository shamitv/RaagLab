# syntax=docker/dockerfile:1
FROM node:24.21.0-bookworm-slim@sha256:2fe369e969550cde8e867afc3fe370b260140cab4a23d467074295b42163d553 AS web-build
WORKDIR /web
RUN npm install --global npm@11.19.0
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY apps/web/ ./
RUN npm run build

FROM web-build AS web-test
RUN npm test

# Browser dependencies remain in this test-only image and never enter runtime stages.
FROM node:24.21.0-bookworm-slim@sha256:2fe369e969550cde8e867afc3fe370b260140cab4a23d467074295b42163d553 AS browser-test
WORKDIR /web
RUN npm install --global npm@11.19.0
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --no-audit --no-fund
RUN npx playwright install --with-deps chromium
COPY apps/web/ ./
COPY scripts/verify-workspace-browser.mjs /web/verify-workspace-browser.mjs
ENV API_BASE_URL=http://api:8000
CMD ["npm", "run", "test:browser"]

FROM python:3.13.15-slim-bookworm@sha256:ed86c82274b3c69b52fb5820f358f0bd7df0b603332063cb5c6e32bd220c3e6e AS python-base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_NO_PROGRESS=1 UV_LINK_MODE=copy
WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.13 && groupadd --gid 10001 museforge && useradd --uid 10001 --gid 10001 --no-create-home museforge
COPY pyproject.toml uv.lock ./

FROM python-base AS api-deps
RUN uv sync --frozen --no-dev --group api --no-install-project
COPY src/ src/
RUN uv sync --frozen --no-dev --group api --no-editable

FROM python-base AS worker-deps
RUN uv sync --frozen --no-dev --group mock-worker --no-install-project
COPY src/ src/
RUN uv sync --frozen --no-dev --group mock-worker --no-editable

FROM python:3.13.15-slim-bookworm@sha256:ed86c82274b3c69b52fb5820f358f0bd7df0b603332063cb5c6e32bd220c3e6e AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/app/.venv/bin:$PATH
WORKDIR /app
RUN groupadd --gid 10001 museforge && useradd --uid 10001 --gid 10001 --no-create-home museforge && mkdir -p /var/lib/museforge/artifacts && chown -R 10001:10001 /var/lib/museforge
COPY alembic.ini ./
COPY migrations/ migrations/
USER 10001:10001

FROM runtime AS api
COPY --from=api-deps /app/.venv /app/.venv
COPY --from=web-build /web/dist /app/web
EXPOSE 8000
CMD ["uvicorn", "museforge.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime AS mock-worker
COPY --from=worker-deps /app/.venv /app/.venv
CMD ["python", "-m", "museforge.worker"]

FROM python-base AS test
RUN uv sync --frozen --group api --group mock-worker --no-install-project
COPY src/ src/
RUN uv sync --frozen --group api --group mock-worker --no-editable
COPY alembic.ini ./
COPY migrations/ migrations/
COPY tests/ tests/
COPY compose.yaml compose.yue2.yaml compose.yue2.gpu.yaml compose.yue2.test.yaml ./
COPY packaging/ packaging/
COPY scripts/ scripts/
COPY .gitattributes .gitignore .dockerignore .env.example ./
COPY --from=web-build /web/dist /app/web
CMD ["/app/.venv/bin/pytest", "tests/unit"]
