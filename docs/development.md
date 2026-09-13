# Foundation development

## Service boundaries

`src/museforge` is one Python distribution with separate API and mock-worker dependency groups. The API image has FastAPI/Uvicorn and database dependencies; the worker image has Celery and database dependencies. Neither includes Node, inference frameworks, or model weights. The dispatcher uses the worker image as a separate process. Vite builds the SPA in a pinned Node stage and the API serves the copied output.

PostgreSQL is authoritative. Run migrations through `python -m museforge.db.migrate`, normally via `bash scripts/migrate.sh`; bare Alembic intentionally refuses execution without the guarded connection. A session advisory lock serializes migration commands, including initial schema creation and singleton workspace setup. Future migrations must not modify `0001_foundation`.

Worker/dispatcher process probes check PostgreSQL, the schema, and an authenticated broker connection. Their observations expire in PostgreSQL and in container health files. Provider registrations remain `initializing` with capability revision `foundation-no-generation`: no provider has been implemented. The dispatcher does not publish outbox jobs yet. The named generation task rejects messages to a bounded quarantine queue instead of returning a simulated success.

Celery remote control is disabled because its transient non-exclusive pidbox queues are rejected by RabbitMQ 4.3 defaults. Readiness uses persisted probes, not `celery inspect`. No result backend, eager execution, implicit queues, or generic Celery retries are enabled.

## Configuration and storage

Copy defaults through `bash scripts/setup.sh`; it preserves an existing `.env`, including when prerequisite checks fail. Credentials in `.env.example` are local development placeholders. Keep PostgreSQL/RabbitMQ credentials consistent with their application URLs. Configuration rejects unsupported real providers, non-CPU devices/model IDs in foundation, relative storage paths, non-loopback host binding, and inconsistent execution timing limits.

The application container paths in `.env.example` match Compose mounts. The API mounts artifacts read-only; the worker mounts the same volume writable. PostgreSQL 18 uses the named volume at `/var/lib/postgresql`, with its data under `18/docker` ([official image documentation](https://hub.docker.com/_/postgres)). RabbitMQ uses a stable hostname and its own persistent volume. DB/broker publish no host ports. Normal `stop.sh` never removes volumes.

`/health/live` measures the HTTP process. `/health/ready` requires reachable DB, exact schema head, the configured local workspace, and readable artifact storage; broker/dispatcher/worker observations are reported separately. The `generation` field is always `not_implemented` in foundation. No generation endpoint is advertised in OpenAPI.

Only documented SPA routes receive HTML fallback. Unknown API paths, missing assets, invalid project UUID paths, and unsupported routes return 404. Hashed assets have immutable caching; HTML and unhashed assets revalidate.

## Local development and tests

Install uv 0.12.13 into your preferred isolated tool environment. It obtains the pinned Python version from `.python-version`.

```bash
uv sync --frozen --group api --group mock-worker
bash scripts/test.sh unit
```

Use the baseline's Node 24.21.0 and npm 11.19.0 for release-equivalent builds. Container stages enforce these versions. A Vite development server is optional and proxies `/health` and `/api` to the local API:

```bash
cd apps/web
npm ci --no-audit --no-fund
npm run dev
```

To run the API locally against explicitly configured local service URLs, set absolute `WEB_DIST` and `ARTIFACT_ROOT`, then run:

```bash
uv run --frozen --group api uvicorn museforge.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Generate TypeScript types from the actual foundation OpenAPI:

```bash
mkdir -p test-results
uv run --frozen --group api python -c 'import json; from museforge.api.app import create_app; print(json.dumps(create_app().openapi()))' > test-results/openapi.json
(cd apps/web && npm run types:api)
```

## Packaged verification

```bash
bash scripts/setup.sh
bash scripts/test.sh integration
```

The Python runner uses a fresh `museforge-foundation-test-<uuid>` Compose project and an automatically allocated loopback API port. It overrides `.env` connection settings and credentials for every test service. It clean-builds the images, runs unit and real-service integration tests, inspects package inventories, and repeats integration checks after an ordinary `down`/`up`. Its `finally` cleanup removes only that generated test project and its volumes. A failed assertion exits nonzero.

Frontend tests in the pinned build runtime can also run with:

```bash
docker build -f packaging/Dockerfile --target web-test .
```

Browser shell checks use the actual API origin (start the mock stack first):

```bash
(cd apps/web && npm ci --no-audit --no-fund && npx playwright install chromium)
(cd apps/web && API_BASE_URL=http://127.0.0.1:8000 npm run test:browser)
```

These checks cover navigation/refresh, no overflow at 1440/390/320 px, browser errors, and automated axe checks. They do not claim the full Phase 03 accessibility or Phase 06 browser acceptance.

## Remote Linux execution

The authoring host has no Docker engine. The user-provided development VM at `10.42.0.42` is reachable as `yolo1` with a key in the ignored `secrets/` directory. Use the same checkout and commands on the VM; do not copy keys, a developer `.env`, weights, or generated audio into the build context. The implementation verification directory is `/home/yolo1/raaglab-foundation-20260913`.

For browser access to a remote loopback port, forward that port over SSH and point `API_BASE_URL` at the local tunnel. Do not widen the Compose host binding. The evidence record names exact tested engine, Compose, runtime, schema, and verification results.
