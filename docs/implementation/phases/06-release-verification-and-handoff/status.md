# Phase 06 status

- State: in_progress
- Started: 2026-09-15
- Last updated: 2026-09-15
- Completed: not yet
- Current focus: finish CPU/release verification gaps, satisfy host prerequisites, and certify the final committed revision

## Completed work

Tasks **06-01, 06-03, 06-07, 06-08, and 06-09** are complete for this checkpoint.
The mock release runner, clean-checkout lifecycle, initial documentation, and
deployment handoff are delivered. CPU device selection, normal-mode verification,
resource preflight/sampling, and stop/start checksum checks are implemented but
still need corrections and runtime verification.

The [mock release record](../../evidence/06/20260915-104002-622828de/README.md)
certifies `c7b2a87c55d1c80b2142c7bd179adff9290808ff` for its recorded mock gate:
42 command outcomes passed, migration head `0004_worker_runtime`, and successful
Compose cleanup. Integration/recovery, frontend, API-served Chromium, documented
lifecycle, and mock restart/update persistence ran. Ten focused runner/deployment
checks also passed; some deployment checks assert source text rather than behavior.

## Remaining work

Tasks **06-02, 06-04, 06-05, 06-06, 06-10, and 06-11** remain open or partial:

- Finish the dated dependency review and implementation corrections listed in
  the [plan](plan.md): device/provenance alignment, inference/watchdog deadlines,
  normal settings assertions, timing/log retention, interruption handling, and
  resource ownership plus final cleanup reporting.
- Add and run CPU browser playback/seek/download/refresh/reopen and lifecycle
  persistence checks on a host meeting the model prerequisites.
- Publish individual A01–A12 and phase results, CPU resource/timing measurements,
  and final-run logs/screenshots. The latest summary is aggregate; its published
  screenshots are from the earlier same-day run.
- Verify the final committed candidate, refresh its tested commands and reports,
  then mark complete. Existing D04/D05 results keep their original scope.

## Runtime blocker

The selected VM `yolo1@10.42.0.42` is reachable with its configured ignored SSH
key. The recorded inspection found 10 GiB total RAM and no external verified
`musicgen-yue2-test_weights` volume. CPU preflight ran and exited 1 at 7.2 GiB
available versus the required 32 GiB; no model container started. See the
[blocked preflight](../../evidence/06/20260915-cpu-gate-blocked/README.md).

WebKit was unavailable and remains optional/unclaimed. Normal-mode CPU inference
and its measurements are unrun. Historical short CPU smoke is not evidence for
this normal-mode gate.

## Next action

Finish the implementation/evidence follow-ups, recheck available host memory and
pinned weights, then run `bash scripts/test.sh release --revision HEAD --real-cpu`
on the final candidate. See the [checklist](todo.md) and
[implementation report](implementation-status.md).
