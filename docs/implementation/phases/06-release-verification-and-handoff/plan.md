# Phase 06: Release verification and handoff

- Updated: 2026-09-15
- State: completed
- Implementation revision: `4b2d42599168925a4771dfc61901c4ad5456abd2`
- CPU model revision: `735c960d9a52b17023271e126b14a65bce2e01ed`
- Evidence: [dated completion package](../../evidence/06/20260915-phase6-completion/README.md)

## Objective

Reproduce the API-served application from a committed disposable checkout,
verify the pinned YuE2 route on CPU with durable evidence, complete browser and
lifecycle checks, and provide accurate operating and deployment handoff
instructions. Public APIs, product schemas and migrations remain unchanged.

## Completed implementation

- Deployment mode selection stores one value and consistently propagates
  explicit CPU/auto/CUDA choices. Automatic fallback remains available and
  strict CUDA startup fails without substituting mock services.
- Effective Compose deadlines are resolved and asserted: 900 seconds warmup,
  3,600 seconds inference, 1,800 seconds queue, 3,660 seconds watchdog, and
  bounded restart/browser/cleanup commands.
- Normal CPU assertions cover pinned model/decoder, CPU/torch-eager provenance,
  four threads, concurrency one, a 28 GiB worker limit, no GPU allocation,
  normal planner settings, exact lyrics, nontruncated validated audio, API
  range/HEAD and download checksums, and stop/start persistence.
- Release commands have unique bounded logs, process-group timeout termination,
  Docker label ownership checks, external-weights protection, partial evidence
  retention, and final cleanup status.
- The real-provider browser test covers play, seek, download checksum, refresh,
  and project reopening. Responsive, keyboard, reduced-motion and native zoom
  checks remain in the mock recovery gate.

## Verification result

The committed mock release passed 42 outcomes. On Ubuntu1 WSL, memory was raised
to 40 GiB and 37.06 GiB was available; the pinned external weights volume was
present. The normal CPU model run passed at `735c960`, including the accepted
audio and lifecycle checks. After the browser Compose profile correction, a
targeted Chromium run against an existing completed YuE2 artifact passed at
`4b2d425`; a no-model Compose configuration check also passed.

The user explicitly stopped the second full CPU invocation before model startup,
so the evidence package identifies the CPU and final browser revisions
separately rather than implying an unperformed combined run. The correction was
isolated to the browser Compose profile and its affected browser gate was
rerun. WebKit was unavailable and remains optional/unclaimed.

## Acceptance

| Criterion | Result |
| --- | --- |
| 06-AC1 clean build/start | Passed committed mock lifecycle and CPU host/weights preflight. |
| 06-AC2 full acceptance | A01–A12 individually mapped in the evidence package. |
| 06-AC3 persistence | Mock rebuild/update and CPU stop/start audio checksum passed. |
| 06-AC4 accurate docs | Operating instructions, handoff, requirements map and dependency review updated. |
| 06-AC5 honest tracking | Tested revisions, optional WebKit, and interrupted rerun are recorded. |
| 06-AC6 deployment handoff | Existing deployment handoff retained with its documented scope. |
| 06-AC7 delivery | Development branch is ready for fast-forward merge; no remote push performed. |

Run the independent mock gate with `bash scripts/test.sh release --revision HEAD`.
The expensive `--real-cpu` command was not repeated after the profile-only fix at
the user's direction; see the exact evidence and scope note above.

See the [master plan](../../master-plan.md),
[requirement matrix](../../requirements-matrix.md),
[status](status.md), [implementation report](implementation-status.md),
[to-do list](todo.md), [deployment handoff](../../../deployment-handoff.md),
and [dependency review](../../dependency-review-2026-09-15.md).
