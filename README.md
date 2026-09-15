# MuseForge AI

A portable local music workspace. Phases 03–04 provide a responsive composer, real audio controls, exact lyrics editing, immutable iterations, searchable Projects and Library, revisioned workspace settings, and multi-tab draft recovery. FastAPI serves the compiled UI with durable PostgreSQL jobs, RabbitMQ dispatch and a separate CPU mock worker. Demo audio does not sing the supplied lyrics or faithfully implement musical controls.

## Start the foundation

Use a Linux Docker engine with the Compose plugin (minimum 2.24.4). No GPU, weights, token, host Python, or host Node installation is required to start the containers.

```bash
bash scripts/setup.sh
bash scripts/start.sh mock
```

Open the loopback URL printed by the start script (default `http://127.0.0.1:8000`). Setup creates a private `.env` only when absent. Change `APP_PORT` in it if necessary. The API listens on `0.0.0.0:8000` inside its container; only its host port is published, on `127.0.0.1`.

```bash
bash scripts/migrate.sh      # safe repeated, serialized schema upgrade
bash scripts/logs.sh         # recent application process logs
bash scripts/stop.sh         # preserves database, broker, and artifact volumes
```

The `mock` profile selects the CPU worker. An explicit `yue2` Compose override selects the integrated YuE2 worker for English, user-supplied lyrics; it has passed durable queued-generation checks on CUDA and short CPU smoke mode. Those narrow checks prove routing and technical audio handling, not lyric adherence, instrumental-only output, style fidelity, or duration control. Missing model files or GPU access fail startup rather than returning demo audio. Run `bash scripts/seed-demo.sh` to create three source-labelled demo projects, or `bash scripts/smoke.sh mock` for a measured audio smoke check. Both use `API_BASE_URL` (default http://127.0.0.1:8000). The mock release gate is `bash scripts/test.sh release`; add `--real-cpu` for the normal-mode CPU model gate when the pinned weights volume and memory prerequisites are available.

## Verify

```bash
bash scripts/test.sh unit          # local uv 0.12.13, Python 3.13.15, Node 24/npm 11
bash scripts/test.sh integration   # isolated Docker project, real PostgreSQL/RabbitMQ
bash scripts/test.sh e2e           # pinned API-served browser plus recovery/restart acceptance
```

Integration performs clean image builds, package/service boundary checks, schema and concurrent migration tests, API-hosted static checks, and ordinary stop/start persistence verification. It deletes only its uniquely named test project and volumes. It overrides application connection settings so it cannot use a configured external database.

The portable application remains mock-first and does not require a GPU or model
weights. The optional YuE2-3B application worker selects CUDA at startup and
falls back to CPU when CUDA is unavailable. Run `bash scripts/test.sh yue2-cpu`
for a real short-audio integration test without a GPU; verified weights and
sufficient RAM are required. See [device configuration](docs/development.md#yue2-cuda-first--cpu-fallback), the
[Part 2 deployment plan](docs/deployment/master-plan.md), [model integration
boundary](docs/model-integration.md), [queued application evidence](docs/deployment/evidence/2026-09-14-d03-review-corrections/README.md),
and [YuE2 evidence](docs/deployment/evidence/2026-09-14-yue2/README.md).

Run `bash scripts/test.sh release` on a reachable Linux Docker engine for the
isolated Phase 06 mock gate. Add `--real-cpu` to include normal-mode pinned
YuE2 CPU inference; that option requires at least 32 GiB available memory and
the external verified weights volume. The runner records the exact source,
runtime, lock, image, migration, persistence, browser, and acceptance results under
`test-results/phase6-<run-id>/`; copy the compact report to
`docs/implementation/evidence/06/` when publishing a release. See the
[development instructions](docs/development.md), [deployment handoff](docs/deployment-handoff.md),
[Phase 04 status](docs/implementation/phases/04-projects-versions-and-recovery/status.md),
[Phase 05 status](docs/implementation/phases/05-provider-readiness/status.md), and
[Phase 04 evidence](docs/implementation/evidence/04/2026-09-14-projects-recovery/README.md).
