# Durable jobs, worker lifecycle, and artifact recovery

- Date: 2026-09-14
- State: Phase 04 dispatch, worker, cancellation, retry, and artifact recovery gates passed; see the [Phase 04 report](phases/04-projects-versions-and-recovery/implementation-status.md)
- Owners: Phase 02 implements the initial path; Phase 04 completes the mock-service recovery contract
- Related: [contracts](contracts.md), [verification strategy](verification-strategy.md), [API documentation](../api.md), [development instructions](../development.md)

## Queue envelope and routing

Use one named task, `museforge.execute_generation`, serialized with Celery's JSON task protocol. Its only business argument is a validated envelope, not lyrics/audio/weights. The dispatcher supplies a Celery task ID matching the outbox message UUID. Required envelope fields:

| Field | Rule |
| --- | --- |
| `schema_version` | Integer 1; unsupported versions are rejected/quarantined with an explicit reason |
| `message_id` | UUID identifying this outbox publication intent; duplicate publication retains the same ID |
| `job_id`, `correlation_id` | UUID logical job and trace correlation |
| `dispatch_sequence` | Monotonically increasing per job; workers reject superseded dispatches |
| `dispatched_at` | UTC dispatch timestamp; DB deadlines remain authoritative |
| `provider_route` | Configured provider/capability route bound to the immutable request |

Route mock music to `museforge.mock.v1`; the selected YuE2 adapter uses `museforge.yue2.v1` (future adapters receive their own versioned route). Declare explicit durable queues/bindings and persistent messages. Workers consume only their configured route; disable implicit task queue creation. Validate envelope route against worker registration and the DB snapshot before claiming. Unsupported envelopes go to a bounded-retention quarantine queue on the same broker with safe structured diagnostics; do not run or endlessly requeue them. A valid known job rejected for an incompatible contract becomes visibly failed through reconciliation.

Publisher confirms establish broker acceptance; they do not establish successful consumption. Set mandatory routing and treat returned/unroutable messages as publication failure. RabbitMQ describes these as separate producer and consumer guarantees in its [confirmation documentation](https://www.rabbitmq.com/docs/confirms). Verify broker restart with persistent queues/messages and a persistent broker volume.

## Submission and outbox transactions

1. Validate the client intent and configured capability route. Acquire the scoped idempotency record, then insert project if needed, immutable job, and initial outbox row in one PostgreSQL transaction. Return 202 only after commit.
2. Dispatcher claims a due outbox row using `FOR UPDATE SKIP LOCKED`, a claim token and a short expiry. Commit before network publication; do not hold a DB lock across broker waits.
3. Publish the versioned envelope with bounded network timeout and confirms. Mark it published only when the claim token still owns the row and routing/confirmation succeeded.
4. If publish fails, persist error, publication count, and next attempt. If the process dies before publish or after publish/before marking it, the expired claim is reclaimed. Re-publication may duplicate a task and must be harmless.
5. A reconciliation loop inspects accepted jobs, stale publication claims, overdue unclaimed dispatches, expired execution leases and cancellation grace deadlines. It uses DB state and deadlines; no in-memory scheduler state is essential. Restarting dispatcher reconstructs work from these records.

Retry publication with capped exponential backoff and jitter until a configured queue deadline, not a fixed small retry count that silently strands accepted work. After the queue deadline persist `timed_out` with a dispatch/worker-unavailable reason. If a published job is unclaimed for a reconciliation window, publish a fresh dispatch sequence transactionally; delayed older messages fail the sequence check. Avoid churn while the worker has a valid claim. All timestamps/deadline comparisons use PostgreSQL time.

## States, stages, and terminal decisions

| State | Entry / next states |
| --- | --- |
| `queued` | Committed request; claim -> running, queued cancellation -> cancelled, queue deadline -> timed_out |
| `running` | Valid claim; success -> succeeded, retryable error -> retrying, fatal error -> failed, deadline -> timed_out, cancel -> cancellation_requested |
| `retrying` | Durable next-attempt schedule; due execution -> running; cancel -> cancelled; expired budget/deadline -> failed/timed_out |
| `cancellation_requested` | Persisted running cancellation; cooperative stop or grace expiry -> cancelled; never becomes succeeded |
| `cancelled`, `succeeded`, `failed`, `timed_out` | Terminal; repeat reads/cancel commands preserve the outcome |

Dispatch status (`pending`, `publishing`, `published`, `abandoned`) and stage (`awaiting_worker`, `writing_lyrics`, `composing_music`, `validating_audio`, `saving_result`) are separate from job state. Progress is null unless the provider reports meaningful work completed. Mock defaults to stage labels and indeterminate progress, with controlled progress mode only for tests. Do not invent queue positions or inference percentages.

Use one lock order for lifecycle transactions: project, job, then attempt/outbox/artifact rows when needed; cancellation and reconciliation use the same order. Success and cancellation both lock the job. If success commits first, cancel returns succeeded. If cancellation commits first, the finalization predicate rejects success and attached output. Terminal states never oscillate. User retry is a new job, never a mutation that resets a failed job.

## Claim, heartbeat, and fencing

A worker transaction checks nonterminal/due state, dispatch sequence, route, cancellation, deadline, and attempt limit, then increments attempt count and a monotonically increasing fence token. Insert an attempt row and establish a bounded lease. Duplicate deliveries to an already claimed/terminal job return without generating or inserting another version. Repeated deliveries do not increment attempt count unless a new claim is legitimately acquired.

Every heartbeat/progress/checkpoint/finalization write compares job ID, attempt token, permitted state and unexpired lease. A worker that cannot renew loses publication authority. Temporary failures do not grant a stale process the right to overwrite a later attempt. Finalization verifies the fence after artifact publication and before inserting the version. An expired attempt may leave a file; it cannot attach it to a successful result.

The mock CPU worker starts with prefork concurrency 1 and prefetch 1. Initialize providers and heartbeat facilities in the execution child. A separate heartbeat loop in that process renews the DB lease and checks cancellation while provider work proceeds. Use short DB transactions/timeouts and a thread-safe cancellation token. If work blocks heartbeat or ignores cancellation, deadlines and fencing still prevent late publication; a watchdog terminates/restarts a stuck execution child within its hard deadline.

The integrated YuE2 worker runs one active inference on its configured GPU and
uses a supervised child for model inference. It performs CUDA/BF16/weight/model
preflight before readiness, keeps lease heartbeat and cancellation checks active,
and reaps the inference process on cancellation, deadline, or owner loss. Its
measured runtime and resource limits are recorded in the [D03 evidence](../deployment/evidence/2026-09-14-d03-review-corrections/README.md).
Additional GPU providers must verify their own process model; never initialize
GPU weights in a parent and then fork arbitrarily, and prove heartbeat/cancellation
responsiveness under busy inference.

## Retry and acknowledgment policy

Use `task_serializer=json`, `accept_content=[json]`, `task_acks_late=true`, `task_acks_on_failure_or_timeout=true`, `task_reject_on_worker_lost=false`, `worker_prefetch_multiplier=1`, and `task_ignore_result=true`; configure no result backend and no eager execution. Suppress task argument/result bodies in logs; log IDs, stage, attempt and safe error codes. The envelope contains no full prompt/lyrics.

The [Celery task guide for the selected release path](https://docs.celeryq.dev/en/v5.6.3/userguide/tasks.html) notes that late acknowledgment does not prevent acknowledgment on child termination. The application deliberately relies on lease reconciliation for these losses. Keep generic automatic Celery retries off: on a recognized transient error, atomically record the failed attempt, change the job to retrying and schedule a new outbox message. Only after this commit may the handled task return/acknowledge. If that transaction cannot commit, DB lease expiry remains the recovery path.

Use at most 3 execution attempts including the first, with delays based on 2 and 4 seconds, jitter, and a 30-second cap. Do not retry validation, unsupported capabilities, missing required model configuration, malformed media or ordinary resource exhaustion. Resource exhaustion is surfaced with a safe configuration hint, not repeated until the machine fails. An unexpected process death is retryable only within the same persisted attempt limit. Exhaustion produces a visible failed outcome (`worker_lost`/last typed reason). Deadline exhaustion produces timed_out.

## Initial configurable limits

| Setting | Mock default | Purpose |
| --- | --- | --- |
| Dispatcher poll / reconciliation interval | 1 s / 5 s | Prompt publication and bounded recovery |
| Outbox claim / broker confirm timeout | 15 s / 5 s | Reclaim interrupted publication |
| Published-unclaimed reconciliation | 60 s | Recover missing task deliveries without rapid duplicate churn |
| Queue deadline | 900 s | Accepted unavailable-worker requests do not wait forever |
| Heartbeat / execution lease | 5 s / 30 s | Bounded orphan ownership |
| Attempt deadline / hard watchdog | 60 s / 75 s | A hanging mock cannot hold the worker indefinitely |
| Cancellation grace | 10 s | Visible cancellation even when provider cannot stop promptly |
| Maximum attempts | 3 | Bounded work; not reset by duplicate delivery |
| Artifact orphan grace | 24 hours | Avoid deleting files between publication and DB attachment |

Snapshot execution limits on accepted jobs. Tests override intervals to stay fast but assert production relationships (`heartbeat < lease < hard watchdog`). Real model limits require measured Part 2 configuration, not automatic use of these short mock durations. Recovery bounds assume dependencies are reachable; during an outage the UI says unavailable and reconciliation resumes on recovery. A stopped worker may still compute until terminated after cancellation, but its fenced result cannot succeed.

## Readiness and shutdown

Register actual worker/provider readiness and capability revision in PostgreSQL with 5-second heartbeat and 30-second freshness. Model initialization is `initializing`, not ready. A stopped/stale worker becomes unavailable. API readiness checks its DB/migration/artifact-read dependencies and reports worker/broker/dispatcher degradation separately; existing projects remain served. Accept configured supported jobs with a clear queued/worker-unavailable status and deadline; reject unconfigured routes.

SIGTERM stops accepting new jobs and drains current work for the configured grace. Persist outcomes before acknowledgment where possible. Forced termination leaves reclaimable leases and cannot lose accepted history. Normal stop preserves every named volume. Startup loads no model in the API and uses a single migration command before dependent services. Test broker, dispatcher, API and worker restarts independently.

## Artifact publication, retention, and repair

Use temporary and final files on the same volume. Validate decodability/nonzero samples, duration/rate/channels, content type, byte count and checksum; flush before atomic rename to a unique attempt-specific key. In a subsequent fenced DB transaction attach the artifact and complete the job/version. A crash between file publication and DB commit creates an orphan, never a misleading successful row.

The worker and an explicit maintenance command have write access; the API mount is read-only. Run `python -m museforge.maintenance` for inspection; inspection is the default and makes no deletions. Run `python -m museforge.maintenance --apply` to retire unreferenced tracked objects and delete only objects whose 24-hour grace has elapsed, no version references them, and no live attempt protects the path. `--grace-hours` may raise the grace period but rejects values below 24. Archive retains references; duplication and lyrics-only versions share artifacts. Do not delete any file referenced by any version. Never use a blanket volume reset for cleanup.

Reconciliation detects missing referenced artifacts and records availability metadata without changing immutable generated content. Playback returns an actionable unavailable result; prior projects/lyrics remain readable, and the library exposes `available: false`. Repair requires recovering the original object or explicitly creating a new generation/version. Tests cover traversal, symlinks, invalid IDs, disk/permission failures, crashes before/after rename, shared-artifact retention, missing-object reporting, dry-run inspection and apply safety.

## Failure proof obligations

Phase 02 proves transactional acceptance, confirmed publication, basic claim/fence, duplicate submission/delivery and playable publication. Phase 04 evidence exercises expired outbox claims and confirmed-publish ambiguity, broker/dispatcher restarts, a killed whole worker with bounded lease recovery, expired fences, retry exhaustion, cancellation races, simultaneous completion, shared/missing artifacts, API restart, and full Compose stop/start with named volumes retained. The test-runner only removes its uniquely named Compose projects after saving evidence. Detailed counts and artifacts are in the [Phase 04 evidence](evidence/04/2026-09-14-projects-recovery/README.md).
