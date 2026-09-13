# Phase 02: Mock end-to-end

## Objective

A user can submit a brief and any of the three lyrics modes, see an asynchronous job handled by the separate mock worker, play the returned audio and recover it after refresh. This is the first usable demonstration and must precede visual polish or real-model work.

## Dependencies and entry criteria

Phase 01 runtime/build/migration/static-hosting gates pass. PostgreSQL, RabbitMQ, dispatcher, API and the CPU mock worker run in the documented Compose environment. Read the immutable snapshot, outbox, claim/fence and audio contracts before adding the first job path.

## Scope

A simple usable composer, exact user/static/mock lyrics, real DB/broker/worker transport, valid audible original WAV output, 202 submission and polling, basic persistent projects/versions, idempotency, claim/fencing, cancellation and safe artifact publication. Styling may be simple. This milestone mocks only expensive generation, not storage, HTTP or task transport.

## Work breakdown

1. **02-01** Implement typed provider interfaces and three lyrics adapters; retain user lyrics exactly, use original versioned static text fixtures and deterministic mock generation, and persist a lyrics checkpoint before audio generation.
2. **02-02** Implement deterministic CPU mock WAV generation (5–30 seconds, default 8; 44.1 kHz stereo PCM) with accurate decoded metadata/checksum and original-fixture provenance. Support configurable test-only delays, success, typed failure, timeout and cancellation scenarios.
3. **02-03** Implement projects create/detail, POST /generations and GET /jobs, project versions/detail and capabilities routes. Validate all controls, preserve a complete immutable execution snapshot, allocate the effective seed once and return 202 promptly with stable resource URLs.
4. **02-04** Persist scoped idempotency records, project/job and initial outbox in one transaction. Implement conflicting-key responses and concurrent same-key resolution without duplicate projects/jobs.
5. **02-05** Implement outbox claiming, reliable confirmed JSON publication, durable provider queues, publication backoff and interrupted-claim reclamation. The worker validates envelope schema/route/dispatch sequence and fetches its request only from PostgreSQL.
6. **02-06** Implement transactional attempt claiming, heartbeat/lease/fence checks, state/stage updates, bounded execution defaults, cooperative cancellation and minimal lease reconciliation. Use durable state rather than Celery results; a duplicate delivery cannot create another final version.
7. **02-07** Implement filesystem storage with temporary validation/atomic publication, GET/HEAD artifact streaming and byte ranges. Finalize artifact/version/job under locks and constraints; capture selection epoch/submission sequence from the first release of the schema.
8. **02-08** Build the real composer/lyrics mode editor, Generate action, status polling with backoff, inline error/cancel state and a working basic audio player. Display demo provenance and capability limits; keep unsent controls intact and use relative URLs.
9. **02-09** Add provider/domain tests and real-service tests for 202 timing, the complete transport path, Unicode lyrics preservation, two-project isolation, duplicate request/delivery, failed/cancelled output and range/traversal behavior.
10. **02-10** Run the demonstrable browser checkpoint against the API container: submit, observe queued/running, play/seek/download, refresh and fetch persisted project/job/version. Capture worker correlation, PostgreSQL assertions, browser trace and decoded audio metadata.
11. **02-11** Write initial docs/api.md, docs/architecture.md and fixture provenance; make seed-demo.sh, smoke.sh and test.sh perform their real checks. Update tracking and create the phase report only after the integrated checkpoint passes.

## Contracts and data changes

Implement the generation/job/provider/artifact schemas in ../../contracts.md and queue envelope/state/claim design in ../../job-reliability.md. Add migrations only for gaps found in Phase 01. Every successful job inserts one immutable result; no failed/cancelled job creates a completed version. Basic selection fencing and uniqueness start here even though the exhaustive race suite is Phase 04. Baseline capabilities are sufficient for honest demo controls.

## Acceptance criteria

- **02-AC1:** A browser request returns 202 without waiting for inference, crosses actual RabbitMQ, executes in the worker container and produces PostgreSQL job/version/artifact rows.
- **02-AC2:** All three lyrics modes work; exact submitted Unicode/whitespace/stanza labels survive retrieval and are clearly distinguished from static/mock content.
- **02-AC3:** The returned original demo audio decodes to non-silent samples and its measured duration/rate/channels/bytes agree with API metadata; browser play/pause/seek/download work.
- **02-AC4:** Refresh and API restart preserve accepted jobs and completed results; several queued requests across distinct projects do not exchange outputs.
- **02-AC5:** Same idempotency key/payload and duplicate delivery yield one logical job/result; a conflicting key yields 409; basic failure/cancellation has no misleading version.
- **02-AC6:** Worker/dispatch/stage information and mock limitations are visible; no browser stubs, eager tasks, weights, GPU or paid endpoint are required.
- **02-AC7:** The Phase 02 checkpoint evidence proves the complete UI-to-worker path and is recorded before Phase 03 visual implementation begins.

## Verification

Planned: bash scripts/test.sh unit; bash scripts/test.sh integration with test_generation_pipeline.py, test_lyrics_preservation.py, test_idempotency.py and test_artifacts.py; bash scripts/test.sh e2e with generation.spec.ts; bash scripts/smoke.sh mock. Hold a dedicated worker briefly to observe queued state, then release and correlate the message/job/attempt. Decode the WAV, check HTTP 206/416/HEAD and playback time, restart API and refresh. Record A03/A04 and baseline A05/A07/A09/A10/A12 evidence under docs/implementation/evidence/02/<run-id>/.

## Risks, assumptions, and deferred work

Mock audio is a deterministic audible sample, not faithful composition or exact-lyrics singing. Full recovery/race/GC coverage stays in Phase 04, but unsafe publication or duplicate finalization is not acceptable here. Complete responsive design and semantic iteration controls belong to Phase 03; library/settings/duplicate/archive to Phase 04. Do not postpone this checkpoint for a model or decoration.

See the [master plan](../../master-plan.md), [requirement matrix](../../requirements-matrix.md), [status](status.md) and [to-do list](todo.md).
