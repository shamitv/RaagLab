# D03 YuE2 implementation review

Reviewed: 2026-09-14

Baseline: `5f4147e`, including the uncommitted D03 changes and new packaging files.

Recommendation: **Request changes. D03 acceptance remains incomplete.**

This review identifies five high-priority issues and three additional correctness
issues. Runtime conclusions below distinguish static inspection from executed
verification.

## Findings

### 1. [P1] The integrated worker dependency lock is incomplete

Location: [requirements.museforge.lock](../../../../../../packaging/yue2/requirements.museforge.lock), line 13.

Required transitive dependencies are absent from both worker locks. Comparing the
pinned application dependencies against `uv.lock` identifies missing
`python-dateutil`, `tzlocal`, `prompt-toolkit`, `tzdata`, and `typing-inspection`.
Their dependencies also need resolution.

`Dockerfile.worker` installs with `--require-hashes`, so these unpinned dependencies
will block installation. Counting package declarations and hashes does not
establish dependency completeness.

**Required correction:** Generate a complete Python 3.12 runtime lock against the
pinned inference environment. Verify both installation stages and `pip check` in
a clean image.

### 2. [P1] Compose does not allocate a GPU to the real worker

Location: [compose.yue2.yaml](../../../../../../compose.yue2.yaml), line 58.

The service sets NVIDIA environment variables but declares no GPU device
reservation, `gpus` setting, or NVIDIA runtime. The standalone Compose service
explicitly reserves an NVIDIA GPU.

On the normal Docker runtime, the integrated worker will lack GPU access and fail
its mandatory CUDA startup gate.

**Required correction:** Add an explicit reservation for one NVIDIA GPU. Verify
the resolved Compose configuration and CUDA/BF16 access inside the integrated
image.

### 3. [P1] The dispatcher cannot publish every persisted provider route

Locations: [dispatcher.py](../../../../../../src/museforge/dispatcher.py), line 33;
[worker/app.py](../../../../../../src/museforge/worker/app.py), line 26.

Publication now uses the persisted route, but the shared Celery application
registers only the configured provider queue and disables automatic queue
creation.

If queued mock jobs remain when the dispatcher switches to YuE2, publishing those
jobs encounters an unknown queue. The reverse switch has the same problem.
Publication keeps failing until the jobs expire.

**Required correction:** Give the publisher explicit definitions for both
supported routes while restricting each consumer to its configured queue.

**Regression test:** Publish pending mock and YuE2 outbox entries under each
dispatcher configuration.

### 4. [P1] A delivery to the wrong worker can permanently fail a valid job

Location: [worker/execution.py](../../../../../../src/museforge/worker/execution.py), line 51.

A configured-provider or route mismatch calls
`finish_error(..., 'unsupported_capability')` before claiming the job.

Consequently, a valid YuE2 envelope delivered to a mock worker can terminally fail
the durable job. Its later delivery to the correct worker then does nothing.

**Required correction:** Reject or quarantine incompatible deliveries without
changing the job. Keep delivery compatibility checks separate from failures
encountered by the authorized worker.

**Regression test:** Deliver a real envelope to a mock worker, verify the job
remains queued, then successfully claim it with the matching worker.

### 5. [P1] Hard worker loss can leave GPU inference running

Locations: [providers.py](../../../../../../src/museforge/providers.py), line 203;
[worker/app.py](../../../../../../src/museforge/worker/app.py), line 79.

Inference starts in a new process session. Its process registry belongs to the
Celery pool child that launches it; the parent worker has a separate registry.

If that pool child is killed by a hard watchdog or SIGKILL, its cleanup cannot
run. The parent's shutdown hook cannot find the inference process. Inference can
retain GPU memory while the pool replaces the worker or the durable job retries.

**Required correction:** Add supervision that survives pool-child death, with
bounded process-tree termination and reaping.

**Regression test:** Kill the pool child during inference on Linux. Confirm
inference exits, GPU memory recovers, and replacement work cannot overlap it.

### 6. [P2] The real worker ignores deployment credentials and workspace configuration

Location: [compose.yue2.yaml](../../../../../../compose.yue2.yaml), line 46.

The new service hard-codes the database URL, broker URL, and workspace ID without
inheriting the base application's `.env` configuration.

A deployment using custom credentials or workspace settings therefore starts an
API and real worker with different configurations. The worker fails
authentication or checks the wrong workspace.

**Required correction:** Share deployment configuration with the existing
application services and override only YuE2-specific settings.

**Regression test:** Resolve Compose with non-default credentials and a workspace
ID; verify consistency across API, dispatcher, and worker.

### 7. [P2] Readiness accepts workers with incompatible model revisions

Location: [api/routes.py](../../../../../../src/museforge/api/routes.py), line 53.

Readiness filters registrations by workspace, route, and expiry only. A worker
using an older model or provider revision can make generation appear ready even
though execution rejects snapshots created by the current API.

**Required correction:** Match the provider, provider revision, model ID/revision,
and capability revision required by the configured route.

**Regression test:** Register a healthy worker with the correct route but a
different model revision. Generation must remain unavailable.

### 8. [P2] Recorded model identity is not verified against loaded weights

Locations: [preflight.py](../../../../../../packaging/yue2/preflight.py), line 21;
[providers.py](../../../../../../src/museforge/providers.py), line 245.

Preflight verifies the mounted manifest against the packaged model lock.
Registrations and provenance instead use independently configured model IDs and
revisions.

Those configuration values need only be nonempty. An API and worker configured
with the same incorrect revision can pass compatibility checks, load the pinned
weights, and persist false model provenance.

**Required correction:** Validate configured model and decoder identity against
the verified manifest before readiness, and derive recorded identity from that
verified result.

**Regression test:** Supply a conflicting model or decoder revision and confirm
startup fails before registering ready.

## Verification and remaining acceptance

Python compilation and `git diff --check` passed. The dependency comparison
confirmed missing entries in the runtime locks.

Unit tests could not start because the available Python installation lacks
`pytest`. Docker is unavailable in this shell, so image builds, GPU behavior, and
broker integration were not exercised. Findings concerning those paths are based
on code and configuration inspection.

The added tests do not establish complete dependency installation, mixed-route
publication, wrong-worker rejection, hard worker-loss cleanup, or
compatible-model readiness. The successful child test substitutes fake audio
modules, so it does not verify actual FLAC decoding and WAV transcoding.

After correcting the findings, run the Linux unit/integration and mock regression
suites, then complete the Ubuntu1 acceptance gate: one real API request crossing
PostgreSQL/outbox and RabbitMQ, producing one persisted version with verified
provenance, and supporting full, HEAD, and range retrieval plus browser playback
and seeking.

The existing `in_progress` D03 status remains appropriate. This review does not
change the phase status or implement any of the recommended corrections.

## Disposition after reassessment and corrections — 2026-09-14

The findings were reassessed against the code rather than accepted solely on the
review's recommendation. The D03 series was replayed onto Phase 4 merge
`c546152` in `integration/d03-review-corrections`. The replay preserved Phase 4
source-version linkage, retry behavior, migrations, and completed phase status.

| Finding | Disposition and verification |
| --- | --- |
| 1. Runtime lock | Confirmed and corrected. Added resolver input and regenerated the complete Linux Python 3.12 hash lock against inference constraints. Both image installation stages and `pip check` passed. |
| 2. GPU allocation | Confirmed for the standard Docker runtime; a host default NVIDIA runtime could have masked it. Added one explicit GPU reservation and verified the integrated CUDA/BF16/model gate. |
| 3. Persisted routes | Confirmed for mixed pending routes, rather than a fresh single-provider deployment. A dedicated publisher knows both queues and has a registered default queue; each worker retains its configured consumer queue. Unit message-construction tests and four actual broker publication combinations passed. |
| 4. Wrong worker | Confirmed as a defensive delivery issue; ordinary queue isolation already prevents it. Incompatible routes are rejected before database access; incompatible snapshot identities roll back without changing the job. The database test then completes the same job with a matching synthetic provider. |
| 5. Pool-child death | Confirmed risk, distinct from ordinary cancellation/deadline cleanup. A Linux guardian monitors a control pipe, holds an exclusive inference lock, terminates process groups and escaped descendants, and reaps children. Synthetic SIGKILL, cancellation, deadline, shutdown, and real YuE2 GPU owner-loss checks passed. |
| 6. Deployment configuration | Confirmed for custom deployments. The real service inherits `.env`; provider-specific overrides remain explicit. Custom credentials/workspace and mount-access resolution checks passed. |
| 7. Readiness compatibility | Confirmed and corrected. Readiness matches provider/revision, model/revision, route, capability revision, workspace, and expiry. SQL and actual-registration tests passed; API readiness was observed as offline → initializing → ready. |
| 8. Recorded identity | Confirmed and corrected through validation rather than introducing a new identity schema. Startup compares configured model/decoder identity with the packaged lock and verifies mounted manifest identities and file hashes. Conflicting identity fails startup with exit 78. |
| Additional environment concern | Corrected. Warmup and generation share one effective environment builder for offline access, paths, model identity, memory budget, and offload settings. Both use the same lifecycle guardian. |

The final corrected worker has produced a real durable application result with
one attempt and one version, verified model/decoder provenance, and a measured
48 kHz stereo PCM WAV. Full, HEAD, and range retrieval plus browser playback and
seeking passed. Missing weights/model/device and conflicting identity fail
startup; an unavailable real worker leaves the request queued with no attempt or
result until cancellation. No mock fallback occurred.

Detailed results and reproducible commands are in the
[correction evidence](../../../../evidence/2026-09-14-d03-review-corrections/README.md).
This evidence supersedes the original review's environment limitations; the
original findings above remain as the historical review record.

The final Phase 4-baseline regression run passed 48 integration tests, 30 mock
browser checks, all publisher/broker/worker/full-restart recovery probes, and the
existing smoke check. Local Python passed 131 tests; the runtime test image
passed 129 with two expected skips covered locally. Frontend passed three tests.
Two test-fixture corrections restored API-readable synthetic artifacts and the
outbox invariant of the existing live-attempt GC fixture; production Phase 4
behavior was not changed. D03 remained open throughout corrections and is now
completed because the real application gate and final regressions passed.
