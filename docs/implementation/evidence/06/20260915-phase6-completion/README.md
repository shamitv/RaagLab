# Phase 06 completion evidence

Date: 2026-09-15. The implementation branch was
`codex/phase-6-completion`, with final implementation revision
`4b2d42599168925a4771dfc61901c4ad5456abd2`.

## What was verified

- The committed mock release at `1d2b1ca` passed its 42 recorded outcomes,
  including real PostgreSQL/RabbitMQ recovery, frontend checks, API-served
  Chromium, lifecycle commands, persistence, and ownership-checked cleanup.
  See [mock-release-summary-1d2b1ca.json](mock-release-summary-1d2b1ca.json).
- The normal CPU YuE2 run at `735c960d9a52b17023271e126b14a65bce2e01ed`
  passed readiness, queueing, pinned model/decoder provenance, CPU/torch-eager
  execution, four-thread sampling, concurrency one, the 28 GiB worker limit,
  normal planning settings, exact lyrics, nontruncated validated 48 kHz stereo
  audio, API range/HEAD/download checksum, and stop/start audio checksum.
  The generated WAV is deliberately excluded from Git; retained JSON and logs
  are in [cpu](cpu/).
- The final Compose-profile correction at `4b2d425` was validated with a clean
  merged `config --services` check and a targeted browser run against an
  existing completed YuE2 version in the preserved Ubuntu1 deployment. The
  browser test passed playback, seeking, download checksum, refresh, and
  project reopening. See [browser-run.log](browser/browser-run.log),
  [compose-profile-services.log](browser/compose-profile-services.log), and
  [d03-real-playback.png](browser/d03-real-playback.png).

The second full CPU invocation was intentionally interrupted at the user's
request before model startup. The affected browser correction was therefore
revalidated independently without repeating the expensive model run. The
successful CPU run and the targeted final-HEAD browser run are linked by the
same pinned model, application route, and browser assertion file; their tested
revisions are identified above.

## Measurements and retained assertions

| Evidence | Result |
| --- | --- |
| [host-resources.json](cpu/host-resources.json) | 37.06 GiB available; 32 GiB required; 28 GiB worker limit; four CPU threads |
| [readiness.json](cpu/readiness.json) | real provider transitioned to CPU ready |
| [timing.json](cpu/timing.json) | readiness, queue wait, and submit-to-terminal timings retained separately |
| [worker-inspect.json](cpu/worker-inspect.json) | `DEVICE=cpu`, no GPU requests, `WORKER_CONCURRENCY=1`, 3,600 s deadlines |
| [resolved-deadlines.json](cpu/resolved-deadlines.json) | effective Compose values for API, dispatcher and worker |
| [version.json](cpu/version.json) | pinned YuE2/decoder provenance, exact lyrics, normal settings and audio validation |
| [persistence.json](cpu/persistence.json) | identical API audio SHA-256 before and after stop/start |
| [resource-samples.json](cpu/resource-samples.json) | bounded Docker CPU/memory samples retained |

## A01–A12 mapping

| Criterion | Assertion and retained result |
| --- | --- |
| A01 | Clean setup/build/start/migrate and migration head: mock summary outcomes and `0004_worker_runtime`. |
| A02 | API-served shell, routing, responsive and keyboard checks: [browser.txt](mock/browser.txt) and [workspace-inspection.txt](mock/workspace-inspection.txt). |
| A03 | Real service readiness and playable generated media: [readiness](cpu/readiness.json), [version](cpu/version.json). |
| A04 | Exact persisted user lyrics: `lyrics` in [version.json](cpu/version.json). |
| A05 | Restart/update and saved-state durability: mock lifecycle outcomes plus [persistence.json](cpu/persistence.json). |
| A06 | Immutable version/provider metadata: `provenance` and model/decoder revisions in [version.json](cpu/version.json). |
| A07 | Duplicate/concurrency and ambiguous confirmation: [ambiguous-confirm.json](mock/ambiguous-confirm.json). |
| A08 | Worker-loss and lease recovery: [worker-loss.json](mock/worker-loss.json) and [broker-recovery.json](mock/broker-recovery.json). |
| A09 | Retry/cancel/failure handling: [queued-restart.json](mock/queued-restart.json) and [dispatcher-restart.json](mock/dispatcher-restart.json). |
| A10 | Range/HEAD/API checksum and browser download checksum: CPU verifier and [browser-run.log](browser/browser-run.log). |
| A11 | Responsive, zoom, reduced-motion and keyboard behavior: [browser.txt](mock/browser.txt) and [workspace-inspection.txt](mock/workspace-inspection.txt); Chromium screenshot retained separately. |
| A12 | Provider route, CPU/torch-eager provenance and no fallback: [worker-inspect.json](cpu/worker-inspect.json) and [version.json](cpu/version.json). |

## 06-AC mapping

| Acceptance | Result |
| --- | --- |
| 06-AC1 clean build/start | Passed in the committed mock release; CPU host preflight and weights validation passed. |
| 06-AC2 full acceptance | A01–A12 assertions above passed across the committed mock/CPU gates and final browser correction check. |
| 06-AC3 persistence | Mock rebuild/update and stop/start plus CPU audio checksum persistence passed. |
| 06-AC4 accurate documentation | Operating instructions, handoff, requirements mapping and this evidence package updated. |
| 06-AC5 honest tracking | Tested revisions and the user-requested CPU rerun interruption are stated explicitly. |
| 06-AC6 deployment handoff | Existing deployment handoff retained and linked from the Phase 06 reports. |
| 06-AC7 delivery | Development branch is ready for fast-forward merge; remote push is outside scope. |

WebKit was not available and remains optional/unclaimed. Generated audio,
weights, secrets, and disposable Compose state are excluded from Git.
