# Phase 01 implementation evidence

- Recorded: 2026-09-13T08:36:55+00:00
- Base revision: `768f313745712318eb56144d08c5dbca6b249729`; implementation is the working-tree change described by this report.
- Runtime host: user-authorized VM `<verification-host-address>`, SSH user `<verification-user>`, Linux x86_64, rootless Docker 29.8.0, Compose plugin 5.5.1, overlayfs.
- Remote checkout: `<remote-checkout>`.
- Final isolated test project: `museforge-foundation-test` (removed with its test-owned volumes).
- Preview project: `museforge-foundation-preview`, host port 18080; stopped after browser verification, three named volumes preserved.
- Tested runtimes: Python 3.13.15, Node 24.21.0, npm 11.19.0, PostgreSQL 18.6, RabbitMQ 4.3.5. All four documented image digests pulled/built for Linux amd64.
- Schema head: `0001_foundation`; actual PostgreSQL data directory `/var/lib/postgresql/18/docker`, volume mounted at `/var/lib/postgresql`.

## Commands and results

| Check | Executed command / procedure | Result |
| --- | --- | --- |
| Local unit/build | `PATH=/tmp/raaglab-foundation-tools/bin:$PATH bash scripts/test.sh unit` | 49 pytest tests; frontend typecheck, production build, 2 Vitest tests passed. Local supplemental Node 24.14.1/npm 11.11.0. |
| Pinned frontend | `docker build -f packaging/Dockerfile --target web-test -t museforge-foundation-web-test:20260913 .` | Node 24.21.0/npm 11.19.0 frozen install, typecheck/build and 2 tests passed. |
| Lock generation | `uv sync --group api --group mock-worker`; npm lock-only install in the pinned frontend image | Full Python/npm transitive locks generated; frozen image installs passed. |
| Real-service acceptance | `bash scripts/test.sh integration` | Clean image builds; 49 container unit tests; 8 integration tests before and 8 after ordinary down/up; all passed. |
| Boundaries | Resolved Compose JSON, installed package inventories, Node executable checks | Intended services only; DB/broker have no host ports; API loopback binding; API has FastAPI and no Celery; worker has Celery and no FastAPI; neither has Node or inference dependencies. |
| Migrations | Fresh startup, repeated upgrade, two subprocesses blocked behind the advisory lock then released | One schema head and workspace; constraints for ownership, active/parent versions, numbering, job results, idempotency, attempts, outbox and artifact references passed. |
| Persistence | Workspace identity, persistent JSON broker message, artifact marker; ordinary `down`/`up` | All three survived. Actual PG18 data directory verified. |
| Operator commands | Repeated `setup.sh`, `start.sh mock`, `migrate.sh`, correlated `logs.sh`, `stop.sh` | Passed on preview project; setup retained identical `.env` hash; stop retained all three volumes. |
| Browser | `API_BASE_URL=http://127.0.0.1:18081 npm run test:browser` through SSH forwarding to VM port 18080 | 3 Chromium tests passed: 1440×1000, 390×844, 320×740; API-served navigation/refresh, no browser exceptions, no page overflow, zero axe violations. |

See the [verified source checksums](source-sha256.txt), [captured result excerpts](verification.txt), [desktop](foundation-desktop.png), [mobile](foundation-mobile.png), and [narrow](foundation-narrow.png) screenshots. Desktop and narrow screenshots were also visually inspected. Full transient logs and browser output remain in ignored `test-results/` on the authoring host; the small durable excerpts and screenshots above are the reviewable evidence.

## Findings resolved during verification

1. RabbitMQ 4.3 rejects Celery's optional transient non-exclusive pidbox queue. Disabled unused worker remote control; retained explicit durable generation/quarantine queues and persisted health probes. The next full startup and restart checks passed without changing dependency pins.
2. The documented `WORKER_CONCURRENCY=1` environment string was rejected by an integer Literal. Replaced it with a bounded integer (1 only), added a full `.env.example` loading regression test, and verified the ordinary setup/start path.
3. Test image commands now directly invoke the frozen environment's pytest, avoiding an unnecessary editable reinstall at runtime. Added Alembic's explicit path separator.

## Limits and completion

All six Phase 01 acceptance criteria passed. No required foundation runtime gate is unrun. Two upstream deprecation warnings remain in the selected Starlette/HTTPX unit-test integration; tests pass with the documented pins.

This is the foundation shell and process boundary, not an end-to-end generation product. Provider execution, outbox publication/reconciliation, generation APIs, media streaming, and later product controls remain assigned to Phases 02–06. Full responsive design/keyboard/manual AA acceptance and non-amd64 image execution are not claimed. No real model, weights, GPU configuration, or Part 2 deployment was performed. SSH keys and environment files were excluded from Git and Docker build contexts.
