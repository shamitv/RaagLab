# Phase 06: Release verification and handoff

## Objective

A clean configured checkout can reproduce the complete API-served mock application using tested commands, and the user receives accurate operating/development documentation plus a concrete handoff for machine and real-model deployment.

## Dependencies and entry criteria

Phases 01–05 are completed with evidence-based reports; unresolved required gates keep their owner phase open. A Linux-engine environment and the required browser runner are available for clean release verification. The release must not introduce weights/GPU/paid-service requirements.

## Scope

Release verification of all Part 1 requirements, reproducible mock packaging, finalized developer/API/architecture/model/operational docs, current phase history and explicit Part 2 handoff. This phase does not install host drivers, activate a real model or claim deployment to WSL/native Linux.

## Work breakdown

1. **06-01** Audit the requirement matrix and every phase report against current source/locks/migrations/configuration. Reopen affected phases or add dated corrections for changed implementations or missing evidence; do not certify from old green checks alone.
2. **06-02** Recheck selected dependency/runtime support and relevant fixes; deliberately update necessary pins/digests/locks with affected verification. Record exact source revision, image digests, migration head, effective non-secret configuration and test environment.
3. **06-03** Reproduce documented setup and mock startup from a clean configured checkout with isolated fresh test storage; confirm migration serialization, intended service/profile selection, built UI and loopback/internal network boundaries.
4. **06-04** Run the release test entry point covering A01–A12, including real PostgreSQL/broker/worker transport, package routing/cache/ranges, exact lyrics, version lineage/idempotency/concurrency, interruption recovery/cancellation and honest capabilities.
5. **06-05** Run final API-served desktop/mobile/browser/keyboard/long-content/offline/zoom checks and a user-oriented smoke: create, play/seek/download, refine/branch, select history, save, reopen, favorite/rename/duplicate/archive, settings/templates and restart persistence.
6. **06-06** Verify normal stop/start/update paths preserve database/broker/artifact volumes; inspect ignored/generated/secret files and image build contexts. Exercise artifact maintenance dry-run and safe dedicated test cleanup without resetting user data.
7. **06-07** Finalize README.md, docs/architecture.md, docs/development.md, docs/api.md and docs/model-integration.md with exact tested commands, configuration, service health/logging, snapshot/version/Save semantics, limitations and troubleshooting.
8. **06-08** Write docs/deployment-handoff.md with the proven mock command/URL pattern, image/provider selection, service connections, migrations, artifact/model-cache expectations, worker routing, capability gaps and Part 2 D00–D05 ownership.
9. **06-09** Include Part 2 operational obligations: observed target topology/hardware, actual mock and real browser validation, layered device readiness, measured resource limits, startup/update/rollback plan, coordinated DB/artifact backup and isolated verified restore, explicit portability evidence.
10. **06-10** Publish a compact verification record with command outcomes, evidence links and implemented/tested/mocked/pending split. Keep unrun/blocked checks explicit and do not describe a merely decodable demo as semantically correct song generation.
11. **06-11** Synchronize overall/phase status and final reports, then deliver the start instructions and limitations. Close Phase 06 only when every required Part 1 acceptance gate has evidence.

## Contracts and data changes

No new product contracts are expected; fixes update the owning phase and their schema/version/migration records. The release handoff is an operational contract: one-origin API UI, PostgreSQL authority, durable queue/outbox/worker route, referenced artifact storage, controlled migrations and independently selected providers must stay consistent. Host-specific paths/devices belong only to the later deployment configuration.

## Acceptance criteria

- **06-AC1:** A clean checkout with documented prerequisites builds/starts the mock stack and serves the working UI through the API using the exact recorded command.
- **06-AC2:** All twelve Part 1 acceptance checks and the full required local product actions have current real-service/browser evidence, with no SQLite/eager/frontend-only substitute.
- **06-AC3:** Ordinary refresh/API/stack restart retains projects, versions, active selection and playable audio; safe stop/update instructions preserve volumes.
- **06-AC4:** Documentation accurately describes the implemented code, tested scripts, configuration/errors, fixture provenance and real-provider limitations; no broken internal links or future-only commands are presented as tested.
- **06-AC5:** Every completed phase has an accurate implementation-status.md and synchronized tracking; any required unrun gate remains open instead of being hidden by the release report.
- **06-AC6:** Part 2 receives a concrete machine/model handoff with service/storage/migration/routing contracts and missing capabilities; WSL/native-Linux/real-model deployment is not claimed.
- **06-AC7:** The final delivery states what works, how to start it, what actually ran, where evidence/reports live and what remains pending.

## Verification

Planned: bash scripts/test.sh release followed by review of A01–A12 evidence and the full requirements-matrix.md; reproduce README startup/stop/migrate/smoke from a clean checkout. Run git diff --check and tracked-file/secret/build-context inspections. Validate every documentation link and compare advertised scripts/routes/options to actual implementation. Preserve concise evidence under docs/implementation/evidence/06/<run-id>/ and reference prior phase fault traces where the current revision remains covered; rerun impacted gates when changes invalidate them.

## Risks, assumptions, and deferred work

A clean container list or API docs page is not a release proof. Browser/engine absence keeps required gates open with exact limitations. Dependency support can change between planning and release; review rather than silently using floating latest versions. Subjective audio quality, real music generation, GPU operation, target machine exposure and verified host backup/restore remain Part 2 work.

See the [master plan](../../master-plan.md), [requirement matrix](../../requirements-matrix.md), [status](status.md) and [to-do list](todo.md).
