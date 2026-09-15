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

These checks cover all lyrics modes, actual playback/seek/download, refresh, navigation, no overflow at 1440/390/320 px, browser errors, and automated axe checks. The Phase 06 completion package adds the accepted real-provider CPU browser playback/seek/download/refresh/reopen result.

The release gate combines the pinned frontend unit/build image, real-service
integration and recovery matrix, API-served Chromium projects, and the native
200% zoom/keyboard/clipboard inspection:

```bash
bash scripts/test.sh release
```

Run it only from a clean configured checkout or a dedicated test workspace. It
uses uniquely named Compose projects, fresh volumes, an ephemeral loopback API
port, bounded waits, and removes only those test-owned volumes after writing
evidence. The normal lifecycle portion separately exercises `setup.sh`,
`start.sh`, `migrate.sh`, `seed-demo.sh`, `logs.sh`, `smoke.sh`,
`artifact-gc.sh`, `stop.sh`, rebuild/update, and restart persistence. The
release runner never deletes volumes from an ordinary deployment.

## Phase 04 acceptance and artifact maintenance

Run the full isolated Phase 04 gate on a Linux Docker engine with:

```bash
python3 scripts/verify-phase4.py
```

The runner uses a unique `museforge-phase4-test-<id>` Compose project, builds the pinned API/dispatcher/worker/Python-test/browser-test images, runs Python unit and real-service integration tests, and executes Playwright against the API-served SPA. It then verifies a queued job across API restart, publisher-confirm ambiguity, dispatcher and broker restart, whole-worker loss and lease recovery, full Compose stop/start with database/broker/artifact volumes preserved, and a decoded smoke artifact. It saves JSON/browser evidence to `test-results/` before removing only that unique test project's containers and volumes. Do not point this destructive cleanup step at a normal deployment.

The Python and frontend tests use pinned Python 3.13.15 and Node 24.21.0/npm 11.19.0 images. Browser/Playwright dependencies exist only in the test image and are not copied into API or worker runtime images. To run only the frontend production build/typecheck and unit tests, use `docker build -f packaging/Dockerfile --target web-test .`. Browser projects cover 1440, 390, 360 and 320 px; stateful shared-library/recovery flows run once at desktop width, while route/playback/layout checks repeat at all four widths.

The API's artifact mount is read-only. Run maintenance inside the mock-worker service, which has writable access to the same artifact volume; inspection is read-only by default:

```bash
docker compose --env-file .env --profile mock run --rm --no-deps worker-mock python -m museforge.maintenance
```

Deletion requires `--apply`, retains a minimum 24-hour grace period, and rechecks version references and live worker attempts. A longer period is selected with `--grace-hours <hours>`; lower values are rejected. Inspect the report before enabling apply on the deployment workspace.

```bash
docker compose --env-file .env --profile mock run --rm --no-deps worker-mock python -m museforge.maintenance --apply --grace-hours 24
```

## YuE2 CUDA-first / CPU fallback

The real worker uses the official YuE2 0.1.6 source pinned in
`packaging/yue2/model-lock.json`, with the existing pinned model/decoder weights.
The CUDA-enabled PyTorch image also runs on CPU; API and dispatcher images still
contain no inference dependencies. `DEVICE=auto` probes CUDA availability, BF16,
and tensor computation once at startup, then falls back to CPU if that probe
fails. `DEVICE=cuda` is strict; `DEVICE=cpu` bypasses CUDA. The Compose override
uses `YUE2_DEVICE=auto` by default. BF16 model weights and FP32 VAE are unchanged.

Use `compose.yaml` + `compose.yue2.yaml` with the `yue2` profile on GPU-free VMs.
Add `compose.yue2.gpu.yaml` only on hosts with NVIDIA Container Toolkit to expose
the GPU. Docker cannot fall back from a failed container-level GPU reservation;
omit the GPU override if the host cannot provide it. Verified weights are still
required in the external volume selected by `MUSEFORGE_YUE2_WEIGHTS_VOLUME`,
which defaults to `museforge-yue2-weights`.

Weight checksum/identity failures, model load errors, startup timeouts, and
inference failures do not trigger device fallback. The selected device is kept
before Celery forks; each isolated job uses CUDA `torch` or CPU `torch-eager`.
Readiness reports the actual device and fallback reason, and result provenance
records device, backend, runtime revision, and validation.
For an existing deployment, apply migrations before starting the upgraded
services. Queued jobs remain runtime-revision pinned: drain old 0.1.5 work with
a compatible worker or resubmit it explicitly; the upgrade does not rewrite it.

Real-service integration commands (reference host or another Linux Docker engine):

```bash
bash scripts/test.sh yue2-cpu
bash scripts/test.sh yue2-gpu  # optional, requires GPU passthrough
```

These create unique, disposable PostgreSQL/RabbitMQ/API/dispatcher/worker stacks
with isolated test credentials, verify one queued job and API-served PCM WAV
(including HEAD/range/hash checks), then remove only their own test volumes.
External verified weights and evidence under `test-results/yue2-devices` remain.
For additional offline startup checks, build `museforge-yue2:0.1.6` with
`packaging/yue2/Dockerfile.worker`, then run `python3 scripts/verify-yue2-startup.py`.
It checks strict CUDA without a GPU, explicit CPU, missing weights, identity
mismatch, and warmup timeout without fallback.
CPU execution requires substantial RAM (tested with 28 GiB container limit,
four CPU threads); this is a real 3B model test, not a mock.

The Phase 6 release gate adds a normal-mode CPU generation to the mock release
verification. It requires at least 32 GiB available host memory, keeps the
28 GiB worker limit and four CPU threads, and records readiness, queue,
generation, resource, provenance, audio checksum, and cleanup evidence:

```bash
bash scripts/test.sh release --real-cpu
```

The default `bash scripts/test.sh release` remains mock-only. The release runner
creates a detached checkout at the candidate revision and gives each Compose
project a fresh configuration, unique name, loopback port, and disposable
storage. YuE2 CPU verification requires the external pinned weights volume;
weights and credentials stay outside the checkout. The final tested revisions,
browser correction, and retained evidence are listed in
`docs/implementation/evidence/06/20260915-phase6-completion/README.md`.

`YUE2_TEST_SMOKE=false` is the deployment default. The isolated test overlay
explicitly enables it across services. Smoke jobs freeze the flag in their
snapshot and use `cot=off`, greedy 32-token semantic sampling, and the default
32 synthesis steps. Only smoke validation permits short/truncated audio; it
still requires nonempty, finite, nonzero 48 kHz stereo and a published PCM WAV.
It does not test full-song completion or perceptual quality. Production keeps
full symbolic planning and its original >5-second/nontruncation thresholds.

## Remote Linux execution

The original foundation verification used an authorized remote Linux Docker
host reached through SSH. Review corrections used a separate WSL2 Docker host.
Exact endpoints, usernames, distribution aliases, and checkout paths are kept
only in ignored local documentation. Run the same commands from the repository
root on another Linux engine; do not copy keys, a developer `.env`, weights, or
generated audio into the build context.

For browser access to a remote loopback port, forward that port over SSH and point `API_BASE_URL` at the local tunnel. Do not widen the Compose host binding. The evidence record names exact tested engine, Compose, runtime, schema, and verification results.

## Responsive workspace (Phase 03)

The API serves the compiled React workspace at `/create`, `/projects`, `/projects/{id}`, `/library`, `/settings`, and `/templates`. Each navigation destination uses server-backed project/version state and can be reopened by its persistent route.

The workspace provides capability-derived composer choices, explicit lyrics sources, duration/seed under Advanced Options, a single HTML audio element, seek/volume/repeat/project collection controls, exact lyrics editing, favorite/rename, version selection and four iteration operations. Native browser playback failures and clipboard failures are reported in the page. No synthetic waveform or invented song structure is displayed. A measured artifact duration appears with structure availability; player elapsed/total time comes from the audio element.

IndexedDB stores editable Generation inputs, base server revision, dirty state, edit timestamp, project key, and per-tab identity after a 200 ms debounce and before submissions. Save Project is a conditional server save. A stale `If-Match` conflict keeps the local edit and offers Keep local, Use server, and Save copy. Reconnect reconciles local/server revisions without duplicate generation; IndexedDB failures keep in-memory edits and report that local recovery was not written. Audio is never stored as authoritative IndexedDB data. The composer stays disabled until the initial draft and server context are loaded.

Run the Phase 04 acceptance command above to check projects, completed-version library, settings/templates, draft recovery, retries, API-served playback, and runtime recovery together. Its evidence and acceptance mapping are in `docs/implementation/evidence/04/2026-09-14-projects-recovery/`.

For reproducible visual evidence, run `API_BASE_URL=<API-origin> node scripts/verify-workspace-browser.mjs` after installing Playwright Chromium. It creates a dedicated original demo and writes viewport, clipboard, keyboard, local-font and native 200% zoom observations under `test-results/workspace-inspection`. Set `EVIDENCE_DIR` to change that directory. Concurrent Playwright CLI invocations need distinct `--output` directories to avoid trace-file collisions. Indic font sources and SIL licenses are in `apps/web/src/fonts`; Vite emits hashed font assets served through the API's existing `/assets` route.
