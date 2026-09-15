# Phase 06 release verification — exact committed revision

Date: 2026-09-15. The mock release gate ran on `yolo1@10.42.0.42` from a
disposable clean worktree created from committed revision
`c7b2a87c55d1c80b2142c7bd179adff9290808ff`.

## Result

- Status: **passed**; 42 recorded command outcomes, all return code 0 and no
  timeout.
- Recovery/integration/browser gate: passed in 807.652 seconds, including the
  existing Chromium viewport, keyboard, reduced-motion, native 200% zoom,
  restart, cancellation, retry, and interruption checks.
- Frontend unit target: passed in the container; container Python and Node
  version checks passed.
- Lifecycle: setup, isolated Compose start, migration, seed, smoke, logs,
  artifact-maintenance dry-run, rebuild/update, stop/start persistence,
  migration-head, and image inspection all passed.
- Cleanup: the owned runtime and phase projects were stopped and removed with
  their test volumes; all cleanup outcomes returned 0.
- Migration head: `0004_worker_runtime`.

The run used unique projects
`museforge-phase6-test-75bf5dc1ab` and
`museforge-phase6-runtime-750ea43f86`, an ephemeral loopback API port
(`35155`), and sanitized configuration recorded in `release-summary.json`.
Image IDs and available repository digests are in `image-records.json`; the
individual command results and durations are in `command-outcomes.json`.

The separate normal-mode CPU gate remains explicitly blocked by the target
host prerequisites. Its bounded preflight evidence is in
[`20260915-cpu-gate-blocked`](../20260915-cpu-gate-blocked/README.md). This
mock release result does not claim real-model quality, lyric adherence, or
duration accuracy.
