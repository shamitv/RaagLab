# MuseForge AI

A portable local music workspace. Phase 03 provides a responsive composer, real audio controls, exact lyrics editing and immutable version iterations, served by FastAPI with durable PostgreSQL jobs, RabbitMQ dispatch and a separate CPU mock worker. Save, favorite, rename and version selection persist through the API; drafts recover locally in IndexedDB. Demo audio does not sing the supplied lyrics.

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
```

Integration performs clean image builds, package/service boundary checks, schema and concurrent migration tests, API-hosted static checks, and ordinary stop/start persistence verification. It deletes only its uniquely named test project and volumes. It overrides application connection settings so it cannot use a configured external database.

The portable application remains mock-first and does not require a GPU or model
weights. A separate YuE2-3B standalone GPU image has been built and tested on the
Ubuntu1 WSL2 host; it is not wired into the application queue yet. See the
[Part 2 deployment plan](docs/deployment/master-plan.md), [model integration
boundary](docs/model-integration.md), and [dated YuE2 evidence](docs/deployment/evidence/2026-09-14-yue2/README.md).

See [development instructions](docs/development.md), [Phase 03 status](docs/implementation/phases/03-complete-responsive-workspace/status.md), and [verification evidence](docs/implementation/evidence/03/2026-09-13-workspace/README.md).
