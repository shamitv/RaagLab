# Development

## Service boundaries

`src/museforge` is one Python distribution with separate API and mock-worker dependency groups. The API image has FastAPI/Uvicorn and database dependencies; the worker image has Celery and database dependencies. Neither includes Node, inference frameworks, or model weights. The dispatcher uses the worker image as a separate process. Vite builds the SPA in a pinned Node stage and the API serves the copied output.

PostgreSQL is authoritative. Run migrations through `python -m museforge.db.migrate`, normally via `bash scripts/migrate.sh`; bare Alembic intentionally refuses execution without the guarded connection. A session advisory lock serializes migration commands, including initial schema creation and singleton workspace setup. Future migrations must not modify `0001_foundation`.

Worker/dispatcher process probes check PostgreSQL, the schema, and an authenticated broker connection. Their observations expire in PostgreSQL and in container health files. Provider registrations report ready/busy with capability revision `1`. The dispatcher publishes durable outbox jobs and reconciles leases; the named task runs the fenced mock pipeline. Invalid envelopes are rejected to the bounded quarantine queue. See [architecture](architecture.md).

Each broker probe runs in a disposable subprocess. `BROKER_TIMEOUT_SECONDS` bounds connection setup, channel creation, queue declarations, and connection cleanup together. A timeout kills and reaps the child, records a safe failure category, and allows the next heartbeat to retry. Child output is discarded so broker-controlled errors cannot enter service logs.

Celery remote control is disabled because its transient non-exclusive pidbox queues are rejected by RabbitMQ 4.3 defaults. Readiness uses persisted probes, not `celery inspect`. No result backend, eager execution, implicit queues, or generic Celery retries are enabled.

Consumer diagnostics for unknown messages/tasks, invalid tasks, and decode errors use fixed `consumer_*` codes. The filter removes payload arguments, exception text, and stack details before handlers format the record; unrelated operational logs and Celery's existing acknowledgement/rejection behavior are preserved.

## Configuration and storage

Copy defaults through `bash scripts/setup.sh`; it preserves an existing `.env`, including when prerequisite checks fail. Credentials in `.env.example` are local development placeholders. Keep PostgreSQL/RabbitMQ credentials consistent with their application URLs. Configuration rejects unsupported real providers, non-CPU devices/model IDs in foundation, relative storage paths, non-loopback host binding, and inconsistent execution timing limits.

The application container paths in `.env.example` match Compose mounts. The API mounts artifacts read-only; the worker mounts the same volume writable. PostgreSQL 18 uses the named volume at `/var/lib/postgresql`, with its data under `18/docker` ([official image documentation](https://hub.docker.com/_/postgres)). RabbitMQ uses a stable hostname and its own persistent volume. DB/broker publish no host ports. Normal `stop.sh` never removes volumes.

`/health/live` measures the HTTP process. `/health/ready` requires reachable DB, exact schema head, the configured local workspace, and readable artifact storage; broker/dispatcher/worker observations are reported separately. The `generation` field reports ready/unavailable based on fresh provider observations. Generation endpoints are described in OpenAPI and [API documentation](api.md).

Only documented SPA routes receive HTML fallback. Unknown API paths, missing assets, invalid project UUID paths, and unsupported routes return 404. Hashed assets have immutable caching; HTML and unhashed assets revalidate.

## Local development and tests

Install uv 0.12.13 into your preferred isolated tool environment. It obtains the pinned Python version from `.python-version`.

The repository pins shell scripts to LF with `.gitattributes`, including Windows checkouts using `core.autocrlf=true`. No global Git setting change is required. The checkout regression uses Git on the authoring host; runtime test images intentionally omit Git and skip that single check.

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

Generate TypeScript types from the actual OpenAPI:

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

The Phase 2 Python runner uses a fresh `museforge-phase2-test-<uuid>` Compose project and an automatically allocated loopback API port. It overrides developer connection settings, builds pinned images, runs unit and real-service tests, checks project/audio persistence after an API restart, and executes the smoke client. Set `PHASE2_BROWSER=1` to also run locally installed Playwright browsers against the isolated origin. Evidence is written under `test-results/`; cleanup removes only the generated test project's volumes. A failed assertion exits nonzero.

The original `verify-foundation.py` remains available for package boundaries, malformed consumer log redaction, and full ordinary down/up persistence checks.

Frontend tests in the pinned build runtime can also run with:

```bash
docker build -f packaging/Dockerfile --target web-test .
```

Browser generation and navigation checks use the actual API origin (start the mock stack first):

```bash
(cd apps/web && npm ci --no-audit --no-fund && npx playwright install chromium)
(cd apps/web && API_BASE_URL=http://127.0.0.1:8000 npm run test:browser)
```

These checks cover all lyrics modes, actual playback/seek/download, refresh, navigation, no overflow at 1440/390/320 px, browser errors, and automated axe checks. They do not claim the full Phase 03 accessibility or Phase 06 browser acceptance.

## Remote Linux execution

The original foundation verification used the user-provided VM at `10.42.0.42` as `yolo1`, with a key in the ignored `secrets/` directory. That historical checkout is `/home/yolo1/raaglab-foundation-20260913`; credentials are not present in this checkout. The review corrections use the existing `Ubuntu1` WSL2 distribution and its Linux Docker engine, reachable from PowerShell with `wsl -d Ubuntu1 -- bash scripts/test.sh integration`. Use the same checkout and commands on another Linux engine; do not copy keys, a developer `.env`, weights, or generated audio into the build context.

For browser access to a remote loopback port, forward that port over SSH and point `API_BASE_URL` at the local tunnel. Do not widen the Compose host binding. The evidence record names exact tested engine, Compose, runtime, schema, and verification results.

## Responsive workspace (Phase 03)

The API serves the compiled React workspace at `/create` and `/projects/{id}`. Create and Projects are the working navigation destinations. Library, Settings, Templates, duplicate and archive remain Phase 04 work and are omitted from navigation.

The workspace provides capability-derived composer choices, explicit lyrics sources, duration/seed under Advanced Options, a single HTML audio element, seek/volume/repeat/project collection controls, exact lyrics editing, favorite/rename, version selection and four iteration operations. Native browser playback failures and clipboard failures are reported in the page. No synthetic waveform or invented song structure is displayed. A measured artifact duration appears with structure availability; player elapsed/total time comes from the audio element.

IndexedDB stores editable Generation inputs, base server revision, dirty state and edit timestamp after a 200 ms debounce and before submissions. Save Project is a conditional server save. An initial recovery conflict offers local/server choices; stale saves retain the local draft and expose Reload server state for review. Full multi-tab reconciliation and library organization remain Phase 04. Audio is never stored as authoritative IndexedDB data. The composer stays disabled until the initial draft and server context are loaded.

Run `bash scripts/test.sh unit`, `bash scripts/test.sh integration`, and `API_BASE_URL=<API-origin> bash scripts/test.sh e2e`. Integration includes `test_version_lineage.py`; browser tests cover 1440, 390, 360 and 320 px, intermediate breakpoints, actual playback, native-script lyrics and axe. The isolated integration runner retains the Phase 02 queued/API-restart checkpoint. See the Phase 03 evidence directory for the exact tested environment and results; the existing runtime-version guidance above still applies.

For reproducible visual evidence, run `API_BASE_URL=<API-origin> node scripts/verify-workspace-browser.mjs` after installing Playwright Chromium. It creates a dedicated original demo and writes viewport, clipboard, keyboard, local-font and native 200% zoom observations under `test-results/workspace-inspection`. Set `EVIDENCE_DIR` to change that directory. Concurrent Playwright CLI invocations need distinct `--output` directories to avoid trace-file collisions. Indic font sources and SIL licenses are in `apps/web/src/fonts`; Vite emits hashed font assets served through the API's existing `/assets` route.
