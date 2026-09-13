# Phase 04: Projects, versions, and recovery

## Objective

Users can reliably save, reopen, search and organize a persistent music library, keep every version and local draft, and recover coherently from duplicate requests, service loss, cancellation, retries and conflicting saves.

## Dependencies and entry criteria

Phase 03 workspace actions and required responsive checks pass. The Phase 02 transactional outbox, version/claim constraints and artifact protocol already exist. Fault checks require an isolated named Compose test project and deterministic mock barriers; they must not disrupt an existing user's library.

## Scope

Complete Projects/Library/Settings/Templates, Save semantics, favorites/search/rename/duplicate/archive, multi-tab/local draft reconciliation, explicit retries, robust dispatch/lease recovery, terminal-state races, orphan cleanup and missing-artifact handling. This is hardening of real persistence/reliability, not a replacement with a new queue or storage engine.

## Work breakdown

1. **04-01** Implement complete project listing/search/reopen and GET /library with stable pagination, favorites and filters. Wire desktop search/mobile navigation and preserved project context to real routes and server results.
2. **04-02** Implement project duplication with fresh IDs, copied completed version graph/remapped parents/active selection and shared artifact references; do not copy pending jobs or idempotency/attempt records. Add conditional archive/unarchive, rejecting active-job conflicts.
3. **04-03** Implement GET/PATCH settings with revisions and honest generation/playback/export defaults; provide a small original versioned template catalogue. Applying templates changes the draft without automatic generation.
4. **04-04** Complete conditional Save Project for title/draft/selection/organization, inline success/failure, IndexedDB local autosave/base revision and reconnect reconciliation. Handle two-tab 412 conflicts with explicit keep-local/use-server/save-copy choices and no silent loss.
5. **04-05** Implement explicit failed/timed-out job retry as a new idempotent linked job using the preserved request/lyrics checkpoint; finalize bounded automatic attempt scheduling/backoff/error classification and inspectable attempt history.
6. **04-06** Complete outbox publication-claim reclamation, unpublished/published-unclaimed reconciliation, broker outage/restart recovery and durable route/schema failure handling with clear deadline outcomes.
7. **04-07** Complete execution leases/heartbeats/fencing, child and whole-worker loss detection, hard watchdog/drain behavior, queue/running timeouts and cancellation grace. Verify every conditional write rejects stale/superseded owners.
8. **04-08** Prove lock ordering, concurrent version-number allocation, unique final result per job and automatic activation versus manual-selection epoch/latest-submission rules. Exercise old/duplicate queue messages without duplicate content.
9. **04-09** Implement artifact orphan/retirement inspection and explicit GC dry-run/apply commands, reference-aware retention, missing-object availability and error handling. Protect shared duplicate/lyrics-only audio and attach/delete races.
10. **04-10** Add deterministic real-service fault tests for the commit/publish gap, ambiguous confirms, lost worker, stale late completion, bounded retries, cancel-before-start/cancel-during/cancel-success races, simultaneous completions and disk/permission failures.
11. **04-11** Run complete Save/reopen/library/settings/template/iteration/offline browser flows and ordinary service restart without deleting volumes; record project/version/attempt/artifact evidence and any environment limitation.
12. **04-12** Update architecture/API/development and recovery documentation with tested semantics/commands, synchronize tracking and create implementation-status.md only after every required persistence/recovery gate passes.

## Contracts and data changes

Implement remaining routes and tables from ../../contracts.md; add immutable migrations for settings/organization/recovery metadata where absent. Preserve scoped idempotency, operation snapshots and existing version content. Use the state machine and production/test limit relationships in ../../job-reliability.md. Archive retains artifacts; duplicates may have origin_version_id and null generation_job_id. Every artifact deletion must prove no references and no live attachment race.

## Acceptance criteria

- **04-AC1:** Projects, Library, Templates and Settings have real search/filter/navigation/save actions; favorite/rename/duplicate/archive/unarchive semantics match the docs and survive restart.
- **04-AC2:** Save/reopen restores selected version and draft while accepted jobs/results already persist; offline and two-tab edits reconcile without silent overwrite or duplicate submission.
- **04-AC3:** Iteration/variation/lyrics edits preserve parentage, previous audio and shared references; simultaneous completions allocate unique numbers and late results respect manual selection.
- **04-AC4:** Duplicate submission/delivery and superseded messages create at most one final version per job; explicit retry is a new linked job and automatic retries keep the logical job.
- **04-AC5:** Accepted committed-but-unpublished work recovers; publisher ambiguity, broker/dispatcher restarts, child/worker loss and stale leases have bounded visible outcomes within the documented dependency-available conditions.
- **04-AC6:** Queued cancellation prevents start; running cancellation, timeout and success races produce one immutable terminal outcome and never attach discarded media; repeated failures/OOM do not loop forever.
- **04-AC7:** Orphan/missing/disk/permission/traversal scenarios are coherent; GC cannot delete shared referenced artifacts; normal stop/start preserves the library.
- **04-AC8:** A05–A10 and changed A11 flows have real PostgreSQL/broker/worker/API-served browser evidence using isolated fault-test data.

## Verification

Planned: bash scripts/test.sh integration for test_persistence_restart.py, test_idempotency.py, test_version_lineage.py, test_concurrent_completion.py, test_dispatch_recovery.py, test_worker_recovery.py, test_job_lifecycle.py, test_cancellation_races.py and test_artifacts.py; bash scripts/test.sh e2e for reopen.spec.ts and library/settings/offline/save-conflict scenarios. Run the barrier-controlled failures in ../../verification-strategy.md and inspect terminal rows, attempt counts, outbox states, version IDs and artifact checksums. Record bounds using shortened test configuration and verify production limit ordering. Evidence goes under docs/implementation/evidence/04/<run-id>/.

## Risks, assumptions, and deferred work

Fault tests can be destructive if pointed at the normal library; require an isolated test project and explicit fixtures. DB/file atomicity requires orphan recovery, not a claim of a cross-resource transaction. IndexedDB may be unavailable/full: report local-save failure and preserve in-memory edits without claiming recovery is guaranteed. Public/multi-user access and host backup/restore remain separate scope.

See the [master plan](../../master-plan.md), [requirement matrix](../../requirements-matrix.md), [status](status.md) and [to-do list](todo.md).
