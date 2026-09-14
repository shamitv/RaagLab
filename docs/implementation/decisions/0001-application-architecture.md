# ADR 0001: Portable application architecture

- Date: 2026-09-13
- Status: accepted for planning; implementation gates remain open
- Scope: Part 1 portable mock application
- Related: [master plan](../master-plan.md), [contracts](../contracts.md), [job reliability](../job-reliability.md), [dependency baseline](../dependency-baseline.md)

## Context

The repository is a product specification and two UI references. The core workflow must survive browser closure and service restarts, preserve every generated version, and eventually run an independently selected local music model. A usable integrated mock milestone must arrive before model acquisition or extensive UI polish. Both WSL and native Linux must use identical application contracts and Linux images.

## Decision

1. Use a small monorepo: one Python project under `src/museforge/`, a React SPA under `apps/web/`, and explicit migrations, fixtures, tests, packaging, and scripts. Python modules separate API, domain, contracts, providers, storage, dispatcher, and worker responsibilities. This is a simplification of the suggested multiple-package tree; it avoids needless publishing/build layers without merging inference into HTTP handlers.
2. Serve Vite's compiled output from FastAPI in the API image. A Node build stage produces static assets; no Node server or inference dependencies are present in the runtime. Relative URLs, bounded polling, explicit SPA route fallback, and range-capable artifact responses provide a single browser origin. A proxied Vite server is development convenience only. FastAPI's [static-file guide](https://fastapi.tiangolo.com/tutorial/static-files/) describes mounting; nested route fallback and error preservation remain application responsibilities with tests.
3. Use PostgreSQL through SQLAlchemy and Alembic. Relational keys and operational columns encode invariants; JSONB stores flexible but versioned snapshots. SQLAlchemy synchronous transactions and psycopg are adequate initially; HTTP work is short and never holds a transaction during audio generation. PostgreSQL, not Celery state or local browser storage, is authoritative.
4. Use RabbitMQ and Celery in a separate worker container. Persist job plus dispatch intent transactionally. The dispatcher publishes JSON-only messages with confirms and reconciles stale dispatch/leases. Application-owned retries use durable scheduled outbox records; no second result store, Celery Beat, Redis, or inference in API background tasks is introduced.
5. Use durable classic queues, persistent messages and one RabbitMQ instance for local development. This provides restart durability, not high availability or protection against loss of the host disk. Provider-specific queues prevent incompatible consumers. A quarantine queue on the same broker isolates malformed/unsupported messages; it is not an additional broker.
6. A filesystem storage adapter publishes audio under immutable attempt-specific keys on a named volume. API reads; worker writes. Referenced files survive stop/restart and version branching. Cross-host workers require shared/object storage behind the interface; a host-local Docker volume is insufficient.
7. Lyrics and music providers are independently configured. Implement user/static/mock lyrics and deterministic audible mock music. Keep capabilities for lyrics text, instrumental output, vocals, exact lyric-conditioned vocals, and audio editing separate. At this decision's initial date no model was selected; the later D03 implementation update below records the selected YuE2 adapter and its limits.
8. API liveness is separate from dependency and worker readiness. Existing projects remain readable while a model warms or a worker is offline. Durable capabilities/readiness advertise availability; accepted jobs receive visible bounded recovery outcomes.
9. Initial security scope is a trusted single-user local workspace, loopback host binding, internal DB/broker, safe development placeholders, ignored secret files, bounded inputs, and artifact traversal protection. Authentication and internet exposure require later scope. Carry `workspace_id` in data and repository methods to preserve an ownership-check boundary without claiming multi-user security.

## Reliability decisions and consequences

The database owns idempotency, immutable request snapshots, attempt claims, leases, terminal outcomes, version-number allocation, and selection fencing. A worker may compute twice after failures; it may publish only one final version per logical generation job. At-least-once delivery does not mean exactly-once inference.

Celery uses JSON, late acknowledgment, prefetch one, no eager execution, and no result backend. Configure `task_reject_on_worker_lost=false` deliberately: DB lease recovery re-dispatches lost work under an attempt limit instead of relying on unbounded broker redelivery. Celery documents that child termination can still acknowledge late-acknowledged tasks. The [task documentation](https://docs.celeryq.dev/en/v5.6.3/userguide/tasks.html) therefore informs, but does not replace, the application recovery design. Version-specific runtime fault tests are required.

The CPU mock worker begins with prefork concurrency one and initializes provider state in the execution child. A heartbeat loop inside that execution process must continue during work. The D03 YuE2 worker uses a supervised inference child, one active request per GPU, readiness preflight, and bounded cancellation/reaping; D04 continues broader workflow and resource verification. No GPU state may be initialized before an arbitrary fork.

## Implementation update — 2026-09-14

The narrow D03 YuE2 application route is implemented using pinned YuE2-3B and
Vae revisions in a separate worker image and durable queue. One real job persisted
and played through the API. This does not verify exact lyrics, vocal behavior,
instrumental-only output, audio language, musical-control fidelity, or requested
duration; Phase 05 records those independently as supported, unsupported, or
unknown. See the [D03 integration evidence](../../deployment/evidence/2026-09-14-d03-review-corrections/README.md).

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| API background inference or in-memory dispatch | Violates isolation and cannot prove durable cross-container processing |
| SQLite integration storage | Cannot establish the required PostgreSQL transactional/concurrency behavior |
| Untracked DB write then broker publish | Leaves an unrecoverable commit/publication gap |
| Celery result backend as product state | Duplicates persistence and fails project/version/domain requirements |
| Separate deployed frontend server | Adds an unnecessary runtime and origin boundary |
| Model selected from the `musicgen` directory name | No evidence of a user/model decision; risks false capabilities and unsuitable hardware requirements |
| Kubernetes or separate workflow orchestrator | No current requirement justifies the extra services |

## Product decisions

Generated content is immutable; titles, labels, favorites, archive state, and active selection are editable organization metadata. Save persists the draft/title/selection with a revision check; accepted jobs/results persist immediately. Lyrics-only edits create a new version that may reuse audio and must disclose that the audio was not recomposed.

At 1440 px, keep the navigation and two main workspace columns but relax the specified column minima. At narrower desktop widths collapse the rail and/or result-card subgrid, not the page into horizontal overflow. Use the written design's 10 px chip corners and all available options even where the mobile artwork depicts only a subset. Omit collaboration, upgrade, notifications, and account controls from Part 1. See [UI behavior](../ui-behavior.md) for the exact responsive and control rules.

## Acceptance and revisit conditions

The early integrated milestone must prove DB/broker/container boundaries using a browser trace, worker correlation, DB rows, and decoded audio. Phase 04 must prove duplicate delivery, dispatch interruption, cancellation races, worker loss, orphan recovery, and concurrent version completion. Phase 05 audits honest capability behavior; Phase 06 reproduces the packaged release from a clean checkout.

Revisit through a new ADR if additional hosts require object storage, measured load requires async database access or another dispatch design, public access introduces authentication, or an explicitly selected model requires a different worker runtime. Record a dated compatibility update for dependency changes. These are triggers for evidence-based changes, not blockers to the documented mock plan.
