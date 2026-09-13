# Phase 01: Foundation

## Objective

A developer can build and start the portable mock stack and load the compiled UI shell through the API. This establishes the real service boundaries before any simulated generation flow is introduced.

## Dependencies and entry criteria

Phase 00 documentation gate is complete; read ADR 0001, contracts, dependency baseline and job reliability. A suitable Linux container engine with the Compose v2 plugin must be reachable before the runtime acceptance gate. The current authoring shell has no docker command on PATH; identify a suitable existing execution environment when implementation starts and record it without assuming Docker Desktop or WSL.

## Scope

Create the Python/React foundation, frozen dependencies, database migration skeleton with core operational entities, configuration, images, named volumes, health/readiness and initial operational scripts. The UI is a built navigable shell, not a claimed generation product. Keep API, dispatcher and worker as separate processes and worker/API images separate.

## Work breakdown

1. **01-01** Create pyproject.toml and src/museforge role modules, apps/web React/TypeScript/Vite shell, test configuration and exclusions for secrets, weights, generated audio, cache and service data. Do not create empty packages just to mirror a suggested tree.
2. **01-02** Apply the selected direct pins from dependency-baseline.md; generate uv.lock and apps/web/package-lock.json in the chosen runtimes. Establish API, mock-worker and development/test dependency groups with frozen installs and no heavyweight inference dependencies.
3. **01-03** Implement validated configuration for DB/broker URLs, local workspace, artifact root, host port/bind, lyrics/music providers, queue routes, log level and future model settings. Write documented .env.example defaults and preserve existing local .env on repeated setup.
4. **01-04** Create Alembic configuration and initial PostgreSQL migration for workspace, projects, jobs/attempts, versions, artifacts/links, outbox/idempotency and worker registrations, with UUID/UTC/FK/unique/index constraints. Add a one-shot migrate command guarded by a PostgreSQL advisory lock.
5. **01-05** Build the API image with a pinned Node frontend build stage and lightweight pinned Python runtime. Serve the compiled shell, explicit client route fallback, documentation/health routes and cache policy; preserve missing API/asset errors.
6. **01-06** Create a CPU mock-worker image/build target and Celery/dispatcher entry points. Configure explicit JSON task names/routes, no result backend/eager execution, broker connection handling and separate process readiness; do not implement inference in the API.
7. **01-07** Define compose.yaml with db, broker, migrate, api, dispatcher and worker-mock (mock profile), persistent database/broker/artifact volumes and internal networking. Publish only 127.0.0.1:${APP_PORT:-8000}:8000; the API listens on 0.0.0.0 inside its container.
8. **01-08** Implement scripts/setup.sh, start.sh, stop.sh, migrate.sh and logs.sh; seed/smoke/test entry points must fail clearly until their actual checks are delivered. API depends on completed migrations; dispatcher/worker also need healthy broker. Validate profile service selection and no volume deletion during normal stop.
9. **01-09** Add meaningful foundation tests for configuration, migration constraints/idempotence, health, static cache/fallback/exclusions and resolved image/service boundaries. Run clean frozen builds and a real-service startup; record actual engine/Compose versions and migration head.
10. **01-10** Update README.md and docs/development.md with tested foundation commands, synchronize phase/overall status, and create implementation-status.md only after all foundation acceptance checks pass.

## Contracts and data changes

Implement the structural database/API/configuration contracts from ../../contracts.md. Introduce /health/live, /health/ready, /openapi.json and UI shell routes. No working generation endpoint is claimed yet. Use PostgreSQL 18's documented image data directory/volume convention and verify persistence at that actual mount; do not reuse an older major's mount layout by assumption. Provider interfaces may be typed skeletons, but they cannot return fake real readiness.

## Acceptance criteria

- **01-AC1:** A frozen clean install/build resolves selected dependencies in the intended Linux images; API/mock installed package inventories contain no inference framework or weights.
- **01-AC2:** Compose resolves only intended services for mock startup; DB/broker remain internal; the API port is loopback-bound; ordinary stop preserves named volumes.
- **01-AC3:** Migrations apply once on a fresh actual PostgreSQL database, are safe to rerun and serialize concurrent invocation; expected keys/indexes/schema head are visible.
- **01-AC4:** DB, broker, dispatcher and mock-worker entry points are healthy/observable; API readiness reflects required storage/schema dependencies without loading a provider model.
- **01-AC5:** The API container serves the compiled shell, nested client navigation refreshes, hashed assets/entry document have correct cache behavior, and missing API/assets are not swallowed by the SPA.
- **01-AC6:** Exact setup/start/stop/migrate commands and environment limitations are recorded; no unrun required runtime gate is marked passed.

## Verification

Planned commands: bash scripts/setup.sh; docker compose --env-file .env --profile mock config; docker compose --env-file .env --profile mock up -d --build; bash scripts/migrate.sh; bash scripts/test.sh unit; bash scripts/test.sh integration (foundation selection). Run test_packaging.py and test_static_hosting.py plus direct nested-route/missing-resource HTTP checks. Inspect actual resolved mounts, image package lists, schema constraints and service logs. Stop/start without volume deletion and assert the migration/workspace survives. Save evidence under docs/implementation/evidence/01/<run-id>/; these commands have not run during planning.

## Risks, assumptions, and deferred work

Dependency metadata resolution is preliminary; actual locks, Linux image pulls and runtime checks remain mandatory. Current Docker availability is unresolved for execution, not for planning. A model-specific Python/runtime is deliberately deferred to Phase 05/Part 2 D03. Deliver the shell and services here; Phase 02 owns working providers, artifact playback and the first browser-to-worker generation.

See the [master plan](../../master-plan.md), [requirement matrix](../../requirements-matrix.md), [status](status.md) and [to-do list](todo.md).
