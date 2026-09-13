# MuseForge AI

A portable local music workspace. Phase 01 provides a navigable React shell served by FastAPI, PostgreSQL migrations, RabbitMQ, and separate dispatcher/CPU-worker processes. Generation and audio playback arrive in Phase 02; service readiness does not imply provider readiness.

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

The `mock` profile selects the CPU worker. Real adapters are not implemented. Demo seed/smoke commands and full release/e2e commands fail explicitly until their corresponding phases are delivered.

## Verify

```bash
bash scripts/test.sh unit          # local uv 0.12.13, Python 3.13.15, Node 24/npm 11
bash scripts/test.sh integration   # isolated Docker project, real PostgreSQL/RabbitMQ
```

Integration performs clean image builds, package/service boundary checks, schema and concurrent migration tests, API-hosted static checks, and ordinary stop/start persistence verification. It deletes only its uniquely named test project and volumes. It overrides application connection settings so it cannot use a configured external database.

See [development instructions](docs/development.md), [Phase 01 status](docs/implementation/phases/01-foundation/status.md), and [verification evidence](docs/implementation/evidence/01/2026-09-13-foundation/README.md).
