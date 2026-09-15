# Phase 06: Release verification and handoff

- Updated: 2026-09-15
- State: in_progress
- Last verified implementation revision: `c7b2a87c55d1c80b2142c7bd179adff9290808ff`
- Current result: mock release passed; normal-mode CPU verification and final certification remain open.

## Objective and scope

Reproduce the complete API-served mock application from an explicit committed
revision in a disposable clean checkout, verify one normal-mode YuE2 generation
on CPU, and deliver accurate operating instructions and deployment handoff.
`bash scripts/test.sh release` remains mock-only. `--real-cpu` opts into the
additional model gate; passing that gate is **required to close this phase**.

No public API, product schema, or migration changes are planned. Defects found
during verification need focused fixes, regression coverage, and corrections in
their owning phase reports. Preserve existing integration/e2e commands,
deployments, external weights, and historical evidence.

## Work completed and recorded evidence

- The release entry point forwards arguments to `scripts/verify-release.py`.
  The runner checks out the requested commit, creates fresh configuration,
  filters child environments, and uses unique Compose projects, loopback ports,
  and isolated test storage.
- The [committed-revision mock run](../../evidence/06/20260915-104002-622828de/README.md)
  passed all 42 recorded command outcomes and Compose cleanup. It exercised
  frozen container tests, real PostgreSQL/RabbitMQ recovery, API-served Chromium,
  frontend tests/build, setup/start/migrate/seed/logs/smoke, artifact-maintenance
  dry-run, and rebuild/update plus stop/start persistence. Migration head:
  `0004_worker_runtime`; Docker 29.8.0; Compose 5.5.1.
- CPU deployment selection and a `--cpu --normal` verifier are implemented.
  They include memory preflight/limits, device/provenance checks, resource
  sampling, durable generation/audio checks, and a stop/start checksum
  comparison. These paths still need the corrections and runtime proof below.
- Ten focused runner/deployment checks passed on the candidate. They cover
  environment filtering, timeout output, failed commands, persistence mutation,
  cleanup failure reporting, shell syntax, and source assertions for device
  selection. Behavioral deployment and interruption coverage remains open.
- README, architecture, development, API, model, and deployment documents were
  refreshed. Merged Part 2 D04/D05 reports remain complete for their recorded
  Ubuntu1 gates; they do not certify the new normal-mode CPU gate.
- The [CPU preflight](../../evidence/06/20260915-cpu-gate-blocked/README.md)
  exited 1 before model startup: 7.2 GiB available versus 32 GiB required. SSH
  works with the configured ignored key; the expected weights volume is absent.

The current mock summary groups A01–A12 into one result. Published screenshots
come from the earlier same-day run, not the latest committed-revision run.
Individual acceptance mapping and preservation of each final run's referenced
logs/screenshots still need completion. Historical test totals are not a new
test inventory for the latest revision.

## Work breakdown and remaining work

Original task identifiers are retained. Partial tasks stay unchecked in the
[to-do list](todo.md).

| Task | Status | Completed / remaining |
| --- | --- | --- |
| 06-01 Requirements and phase audit | Done for this checkpoint | Reports and matrix reviewed; this update corrects completion claims. Repeat the affected audit after remaining fixes. |
| 06-02 Dependencies and reproducibility | Partial | Revision, locks, image IDs/digests, runtime versions, and migration head recorded. Publish a dated official-source support/fix recheck; change pins only with a reason and rerun affected checks. |
| 06-03 Clean mock setup | Done | Committed-revision checkout and isolated documented mock lifecycle passed. |
| 06-04 Release acceptance | Partial | Mock recovery/integration gate passed. Finish runner/CPU correctness and behavioral regressions, then pass normal-mode CPU generation. |
| 06-05 Browser acceptance | Partial | Mock Chromium workflows and workspace inspection ran. Add CPU playback/seek/download/refresh/reopen verification and retain its browser evidence. |
| 06-06 Persistence and cleanup | Partial | Mock rebuild/update and stop/start persistence passed. Finish cleanup safeguards and verify CPU artifacts and saved state survive the required lifecycle. |
| 06-07 Operating documentation | Done for this checkpoint | Core documents refreshed; update exact tested CPU commands and limitations after final verification. |
| 06-08 Deployment handoff | Done for this checkpoint | Service/storage/migration/routing/provider contracts and Part 2 ownership published. |
| 06-09 Part 2 audit | Done | Merged D04/D05 evidence reviewed within its recorded hardware and capability limits. |
| 06-10 Evidence publication | Partial | Mock summary and blocked preflight published. Add individual A01–A12/phase results, referenced evidence, and normal CPU measurements. |
| 06-11 Final closure | Open | Tracking synchronized for this checkpoint. Certify the final committed revision and close only after every required gate passes. |

### Corrections before the final CPU run

1. Align device selection across deployment commands, worker, and verifier.
   `compose.yue2.test.yaml` currently forces the verifier's `DEVICE=auto`,
   conflicting with explicit CPU fallback expectations. Verify saved deployment
   mode reuse and automatic GPU detection with executable tests, including strict
   CUDA failure and preservation of startup fallback without mock substitution.
2. Apply CPU deadlines to the effective Compose configuration. The worker still
   inherits 900-second process/attempt limits and the verifier inherits a
   930-second watchdog. A 3,600-second outer subprocess timeout alone does not
   supply the required per-inference budget. Allow warmup, queueing, inference,
   restart, evidence collection, and cleanup within consistent outer deadlines.
3. Assert normal planning/token settings and nontruncated validated audio, beyond
   the current smoke flag and duration check. Run the API-served real browser
   workflow against the accepted CPU version; the CPU verifier does not yet
   invoke that workflow.
4. Preserve readiness, queue-delay, and generation timing separately: the outer
   CPU verifier currently overwrites the inner `timing.json`. Bound its Docker
   inspection/stats and audio reads, and retain distinct command logs for restart
   steps instead of overwriting them.
5. Validate Docker resource ownership before every destructive cleanup, beyond
   checking project-name syntax. Retain output on interruption and outer timeout,
   handle subprocess descendants, and finalize status only after both Compose
   and clean-worktree cleanup. Add behavioral regressions for these failure paths.
6. Publish a dated dependency review and a complete final evidence package.
   Preserve referenced logs/screenshots before deleting disposable worktrees;
   map each A01–A12 and 06-AC criterion to its assertion and result.

### CPU host prerequisites and required measurements

| Setting / observation | Required for final verification |
| --- | --- |
| Host | `yolo1@10.42.0.42`; inspect resources again before startup |
| Available memory | At least 32 GiB; current record is 10 GiB total and 7.2 GiB available |
| Weights | Pinned model/decoder in verified `musicgen-yue2-test_weights`, mounted read-only; currently absent |
| Device / mode | `YUE2_DEVICE=cpu`, `YUE2_TEST_SMOKE=false`, CPU/`torch-eager` provenance, no GPU allocation |
| Threads / concurrency / limit | Four CPU threads, concurrency one, 28 GiB worker memory limit |
| Deadlines | 900 seconds warmup; 3,600 seconds per inference; compatible outer watchdogs |
| Durable result | One queued generation, exact persisted lyrics, normal settings, validated nontruncated audio, matching download checksum |
| Measurements | Readiness time, queue delay, generation elapsed time, sampled container memory and CPU |
| Browser / persistence | Play, seek, download, refresh/reopen, and saved audio preservation after stop/start; retain mock restart/update coverage |

Missing access, memory, or weights blocks model execution. Resource exhaustion,
deadline failure, or an assertion failure fails the gate. Host readiness does not
close the implementation/evidence follow-ups above.

## Acceptance and verification

| Criterion | Current status / closure requirement |
| --- | --- |
| 06-AC1 Clean build/start | Mock committed-revision run passed; repeat for the final candidate if code changes. |
| 06-AC2 Full acceptance | Mock aggregate passed; individual A01–A12 mapping, CPU runtime/browser evidence, and remaining regressions are open. |
| 06-AC3 Persistence | Mock refresh/restarts/update covered; CPU lifecycle and artifact preservation still need runtime proof. |
| 06-AC4 Accurate docs | Checkpoint corrected; final tested CPU commands, dependency review, and evidence links remain to be published. |
| 06-AC5 Honest tracking | Phase remains in_progress; complete only with current evidence for all required checks. |
| 06-AC6 Deployment handoff | Published; existing Ubuntu1 D04/D05 results retain their original scope. |
| 06-AC7 Delivery | Mock instructions and blockers available; final CPU result and measurements pending. |

After corrections and prerequisites are satisfied, run on the selected host from
the final committed candidate:

```bash
bash scripts/test.sh release --revision HEAD --real-cpu
```

For the independent mock gate, use `bash scripts/test.sh release --revision HEAD`.
Publish evidence under `docs/implementation/evidence/06/<run-id>/`; validate docs
links, advertised commands, tracked/build-context exclusions, and `git diff --check`.
Record optional WebKit separately. The previous passing mock revision is not
certification of later implementation changes or the final merge commit.

## Boundaries

Technical CPU operation does not establish lyric adherence, musical quality,
precise duration control, or broader provider semantics. Existing short CPU smoke
and Ubuntu1 CUDA/deployment evidence retain their narrow scope. No additional
native host installation or portability claim is made by the mock container run.

See the [master plan](../../master-plan.md), [requirement matrix](../../requirements-matrix.md),
[status](status.md), and [implementation report](implementation-status.md).
