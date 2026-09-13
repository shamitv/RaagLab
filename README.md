# MuseForge AI

A portable local music workspace. Phase 02 provides a composer served by FastAPI, durable PostgreSQL jobs, RabbitMQ dispatch, and a separate CPU worker generating playable original demo WAV audio. Results persist across refresh and API restart.

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

See [development instructions](docs/development.md), [Phase 02 status](docs/implementation/phases/02-mock-end-to-end/status.md), and [verification evidence](docs/implementation/evidence/01/2026-09-13-foundation/README.md).
