# Phase 02 to-do

All items are implementation work and remain unchecked. Planning preparation is tracked in Phase 00.

- [ ] 02-01 Implement typed provider interfaces and three lyrics adapters; retain user lyrics exactly, use original versioned static text fixtures and deterministic mock generation, and persist a lyrics checkpoint before audio generation.
- [ ] 02-02 Implement deterministic CPU mock WAV generation (5–30 seconds, default 8; 44.1 kHz stereo PCM) with accurate decoded metadata/checksum and original-fixture provenance. Support configurable test-only delays, success, typed failure, timeout and cancellation scenarios.
- [ ] 02-03 Implement projects create/detail, POST /generations and GET /jobs, project versions/detail and capabilities routes. Validate all controls, preserve a complete immutable execution snapshot, allocate the effective seed once and return 202 promptly with stable resource URLs.
- [ ] 02-04 Persist scoped idempotency records, project/job and initial outbox in one transaction. Implement conflicting-key responses and concurrent same-key resolution without duplicate projects/jobs.
- [ ] 02-05 Implement outbox claiming, reliable confirmed JSON publication, durable provider queues, publication backoff and interrupted-claim reclamation. The worker validates envelope schema/route/dispatch sequence and fetches its request only from PostgreSQL.
- [ ] 02-06 Implement transactional attempt claiming, heartbeat/lease/fence checks, state/stage updates, bounded execution defaults, cooperative cancellation and minimal lease reconciliation. Use durable state rather than Celery results; a duplicate delivery cannot create another final version.
- [ ] 02-07 Implement filesystem storage with temporary validation/atomic publication, GET/HEAD artifact streaming and byte ranges. Finalize artifact/version/job under locks and constraints; capture selection epoch/submission sequence from the first release of the schema.
- [ ] 02-08 Build the real composer/lyrics mode editor, Generate action, status polling with backoff, inline error/cancel state and a working basic audio player. Display demo provenance and capability limits; keep unsent controls intact and use relative URLs.
- [ ] 02-09 Add provider/domain tests and real-service tests for 202 timing, the complete transport path, Unicode lyrics preservation, two-project isolation, duplicate request/delivery, failed/cancelled output and range/traversal behavior.
- [ ] 02-10 Run the demonstrable browser checkpoint against the API container: submit, observe queued/running, play/seek/download, refresh and fetch persisted project/job/version. Capture worker correlation, PostgreSQL assertions, browser trace and decoded audio metadata.
- [ ] 02-11 Write initial docs/api.md, docs/architecture.md and fixture provenance; make seed-demo.sh, smoke.sh and test.sh perform their real checks. Update tracking and create the phase report only after the integrated checkpoint passes.

No task has been removed or moved. If scope changes, keep the original identifier, explain the change and link its destination. See [plan](plan.md) and [status](status.md).
