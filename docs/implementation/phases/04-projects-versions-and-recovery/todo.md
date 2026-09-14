# Phase 04 to-do

- [x] 04-01 Implement complete project listing/search/reopen and GET /library with stable pagination, favorites and filters. Wire desktop search/mobile navigation and preserved project context to real routes and server results.
- [x] 04-02 Implement project duplication with fresh IDs, copied completed version graph/remapped parents/active selection and shared artifact references; do not copy pending jobs or idempotency/attempt records. Add conditional archive/unarchive, rejecting active-job conflicts.
- [x] 04-03 Implement GET/PATCH settings with revisions and honest generation/playback/export defaults; provide a small original versioned template catalogue. Applying templates changes the draft without automatic generation.
- [x] 04-04 Complete conditional Save Project for title/draft/selection/organization, inline success/failure, IndexedDB local autosave/base revision and reconnect reconciliation. Handle two-tab 412 conflicts with explicit keep-local/use-server/save-copy choices and no silent loss.
- [x] 04-05 Implement explicit failed/timed-out job retry as a new idempotent linked job using the preserved request/lyrics checkpoint; finalize bounded automatic attempt scheduling/backoff/error classification and inspectable attempt history.
- [x] 04-06 Complete outbox publication-claim reclamation, unpublished/published-unclaimed reconciliation, broker outage/restart recovery and durable route/schema failure handling with clear deadline outcomes.
- [x] 04-07 Complete execution leases/heartbeats/fencing, child and whole-worker loss detection, hard watchdog/drain behavior, queue/running timeouts and cancellation grace. Verify every conditional write rejects stale/superseded owners.
- [x] 04-08 Prove lock ordering, concurrent version-number allocation, unique final result per job and automatic activation versus manual-selection epoch/latest-submission rules. Exercise old/duplicate queue messages without duplicate content.
- [x] 04-09 Implement read-only-by-default artifact orphan/retirement inspection and guarded `--apply` collection, reference-aware retention, missing-object availability and error handling. Protect shared duplicate/lyrics-only audio and attach/delete races.
- [x] 04-10 Add deterministic real-service fault tests for the commit/publish gap, ambiguous confirms, lost worker, stale late completion, bounded retries, cancel-before-start/cancel-during/cancel-success races, simultaneous completions and disk/permission failures.
- [x] 04-11 Run complete Save/reopen/library/settings/template/iteration/offline browser flows and ordinary service restart without deleting volumes; record project/version/attempt/artifact evidence and any environment limitation.
- [x] 04-12 Update architecture/API/development and recovery documentation with tested semantics/commands, synchronize tracking and create implementation-status.md only after every required persistence/recovery gate passes.

All eight acceptance criteria and verification results are recorded in the [completion report](implementation-status.md) and [evidence](../../evidence/04/2026-09-14-projects-recovery/README.md). No task was removed or moved. See the [plan](plan.md).
