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

The `mock` profile selects the CPU worker. Real adapters are not implemented. Run `bash scripts/seed-demo.sh` to create three source-labelled demo projects, or `bash scripts/smoke.sh mock` for a measured audio smoke check. Both use `API_BASE_URL` (default http://127.0.0.1:8000). Full release acceptance remains Phase 06 work.

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
boundary](docs/model-integration.md), and [dated YuE2 evidence](docs/deployment/evidence/2026-09-14-yue2/README.md).

See [development instructions](docs/development.md), [Phase 04 status](docs/implementation/phases/04-projects-versions-and-recovery/status.md), and [Phase 04 evidence](docs/implementation/evidence/04/2026-09-14-projects-recovery/README.md). Release certification and real-provider readiness remain Phase 05/06 work.
