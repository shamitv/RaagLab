# Phase 01 to-do

All items are implementation work and remain unchecked. Planning preparation is tracked in Phase 00.

- [ ] 01-01 Create pyproject.toml and src/museforge role modules, apps/web React/TypeScript/Vite shell, test configuration and exclusions for secrets, weights, generated audio, cache and service data. Do not create empty packages just to mirror a suggested tree.
- [ ] 01-02 Apply the selected direct pins from dependency-baseline.md; generate uv.lock and apps/web/package-lock.json in the chosen runtimes. Establish API, mock-worker and development/test dependency groups with frozen installs and no heavyweight inference dependencies.
- [ ] 01-03 Implement validated configuration for DB/broker URLs, local workspace, artifact root, host port/bind, lyrics/music providers, queue routes, log level and future model settings. Write documented .env.example defaults and preserve existing local .env on repeated setup.
- [ ] 01-04 Create Alembic configuration and initial PostgreSQL migration for workspace, projects, jobs/attempts, versions, artifacts/links, outbox/idempotency and worker registrations, with UUID/UTC/FK/unique/index constraints. Add a one-shot migrate command guarded by a PostgreSQL advisory lock.
- [ ] 01-05 Build the API image with a pinned Node frontend build stage and lightweight pinned Python runtime. Serve the compiled shell, explicit client route fallback, documentation/health routes and cache policy; preserve missing API/asset errors.
- [ ] 01-06 Create a CPU mock-worker image/build target and Celery/dispatcher entry points. Configure explicit JSON task names/routes, no result backend/eager execution, broker connection handling and separate process readiness; do not implement inference in the API.
- [ ] 01-07 Define compose.yaml with db, broker, migrate, api, dispatcher and worker-mock (mock profile), persistent database/broker/artifact volumes and internal networking. Publish only 127.0.0.1:${APP_PORT:-8000}:8000; the API listens on 0.0.0.0 inside its container.
- [ ] 01-08 Implement scripts/setup.sh, start.sh, stop.sh, migrate.sh and logs.sh; seed/smoke/test entry points must fail clearly until their actual checks are delivered. API depends on completed migrations; dispatcher/worker also need healthy broker. Validate profile service selection and no volume deletion during normal stop.
- [ ] 01-09 Add meaningful foundation tests for configuration, migration constraints/idempotence, health, static cache/fallback/exclusions and resolved image/service boundaries. Run clean frozen builds and a real-service startup; record actual engine/Compose versions and migration head.
- [ ] 01-10 Update README.md and docs/development.md with tested foundation commands, synchronize phase/overall status, and create implementation-status.md only after all foundation acceptance checks pass.

No task has been removed or moved. If scope changes, keep the original identifier, explain the change and link its destination. See [plan](plan.md) and [status](status.md).
