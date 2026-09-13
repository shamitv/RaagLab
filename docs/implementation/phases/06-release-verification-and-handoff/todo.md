# Phase 06 to-do

All items are implementation work and remain unchecked. Planning preparation is tracked in Phase 00.

- [ ] 06-01 Audit the requirement matrix and every phase report against current source/locks/migrations/configuration. Reopen affected phases or add dated corrections for changed implementations or missing evidence; do not certify from old green checks alone.
- [ ] 06-02 Recheck selected dependency/runtime support and relevant fixes; deliberately update necessary pins/digests/locks with affected verification. Record exact source revision, image digests, migration head, effective non-secret configuration and test environment.
- [ ] 06-03 Reproduce documented setup and mock startup from a clean configured checkout with isolated fresh test storage; confirm migration serialization, intended service/profile selection, built UI and loopback/internal network boundaries.
- [ ] 06-04 Run the release test entry point covering A01–A12, including real PostgreSQL/broker/worker transport, package routing/cache/ranges, exact lyrics, version lineage/idempotency/concurrency, interruption recovery/cancellation and honest capabilities.
- [ ] 06-05 Run final API-served desktop/mobile/browser/keyboard/long-content/offline/zoom checks and a user-oriented smoke: create, play/seek/download, refine/branch, select history, save, reopen, favorite/rename/duplicate/archive, settings/templates and restart persistence.
- [ ] 06-06 Verify normal stop/start/update paths preserve database/broker/artifact volumes; inspect ignored/generated/secret files and image build contexts. Exercise artifact maintenance dry-run and safe dedicated test cleanup without resetting user data.
- [ ] 06-07 Finalize README.md, docs/architecture.md, docs/development.md, docs/api.md and docs/model-integration.md with exact tested commands, configuration, service health/logging, snapshot/version/Save semantics, limitations and troubleshooting.
- [ ] 06-08 Write docs/deployment-handoff.md with the proven mock command/URL pattern, image/provider selection, service connections, migrations, artifact/model-cache expectations, worker routing, capability gaps and Part 2 D00–D05 ownership.
- [ ] 06-09 Include Part 2 operational obligations: observed target topology/hardware, actual mock and real browser validation, layered device readiness, measured resource limits, startup/update/rollback plan, coordinated DB/artifact backup and isolated verified restore, explicit portability evidence.
- [ ] 06-10 Publish a compact verification record with command outcomes, evidence links and implemented/tested/mocked/pending split. Keep unrun/blocked checks explicit and do not describe a merely decodable demo as semantically correct song generation.
- [ ] 06-11 Synchronize overall/phase status and final reports, then deliver the start instructions and limitations. Close Phase 06 only when every required Part 1 acceptance gate has evidence.

No task has been removed or moved. If scope changes, keep the original identifier, explain the change and link its destination. See [plan](plan.md) and [status](status.md).
