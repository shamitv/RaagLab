# Phase 06 to-do

Phase 06 implementation is in progress. The mock release and documentation
work are complete; the normal-mode CPU gate is blocked by host prerequisites.
Planning preparation is tracked in Phase 00.

- [x] 06-01 Audit the requirement matrix and every phase report against current source/locks/migrations/configuration; current release evidence and limitations are recorded.
- [ ] 06-02 Recheck selected dependency/runtime support and record exact source revision, lock hashes, image IDs/digests, readiness/migration state, effective non-secret configuration and test environment for the current candidate.
- [ ] 06-03 Reproduce documented setup and mock startup from a clean configured checkout with isolated fresh test storage; confirm migration serialization, service/profile selection, built UI and loopback/internal network boundaries for the current candidate.
- [ ] 06-04 Run the release test entry point covering A01–A12 with real PostgreSQL/broker/worker transport, routing/cache/ranges, lyrics, lineage/idempotency/concurrency, interruption recovery/cancellation, honest capabilities, and normal-mode CPU YuE2.
- [ ] 06-05 Run API-served desktop/mobile/browser/keyboard/long-content/offline/zoom checks and the user-oriented create/play/seek/download/refine/history/save/reopen/library/settings/templates smoke for the current candidate.
- [ ] 06-06 Verify CPU stop/start/update persistence, ignored/generated/secret files and build contexts; exercise artifact maintenance dry-run and dedicated test cleanup.
- [x] 06-07 Refresh operating/development/API/model documentation with tested commands, configuration, service health/logging, persistence semantics, limitations and troubleshooting.
- [x] 06-08 Publish `docs/deployment-handoff.md` with the mock command/URL, service/storage/migration/routing contracts, provider limits and Part 2 ownership.
- [x] 06-09 Audit the merged Part 2 boundary: target topology/device/resource/backup/restore and real-model operational obligations are current, with semantic/native-Linux limitations explicit.
- [ ] 06-10 Publish the compact verification record with current command outcomes, evidence links and implemented/tested/mock/pending/blocked split.
- [ ] 06-11 Synchronize phase and overall status and deliver start instructions and limitations; close Phase 06 only after the CPU gate passes.

No task has been removed or moved. If scope changes, keep the original identifier, explain the change and link its destination. See [plan](plan.md) and [status](status.md).
