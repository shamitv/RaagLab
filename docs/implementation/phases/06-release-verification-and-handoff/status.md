# Phase 06 status

- State: completed
- Started: 2026-09-15
- Completed: 2026-09-15
- Implementation revision: `4b2d42599168925a4771dfc61901c4ad5456abd2`
- Evidence: [20260915 completion package](../../evidence/06/20260915-phase6-completion/README.md)

## Delivered and verified

The Phase 06 runner now creates disposable committed checkouts, isolates
Compose projects and ports, filters child environments, records unique bounded
command logs, terminates subprocess groups on timeout, validates Docker labels
before cleanup, retains partial evidence, and reports cleanup/worktree status.
Deployment mode selection persists one saved CPU/auto/CUDA value, keeps
automatic fallback, and fails strict CUDA startup without substituting mock
services. Effective normal deadlines are 900 seconds for warmup and 3,600
seconds for inference, with compatible queue, watchdog, restart, browser and
cleanup allowances.

The committed mock release passed 42 outcomes. The normal CPU run passed on
Ubuntu1 after WSL memory was raised to 40 GiB: 37.06 GiB was available, the
external pinned weights volume was present, and the worker used a 28 GiB limit,
four CPU threads, concurrency one, CPU/torch-eager provenance, pinned model and
decoder, normal settings, exact lyrics, validated nontruncated 48 kHz stereo
audio, and matching API/download checksums. Audio remained byte-identical after
stop/start. The final browser-profile correction was revalidated with a
targeted Chromium run against an existing completed YuE2 artifact, covering
playback, seeking, download checksum, refresh, and project reopening.

See the [dated dependency review](../../dependency-review-2026-09-15.md),
[deployment handoff](../../../deployment-handoff.md), and
[A01–A12/06-AC mapping](../../evidence/06/20260915-phase6-completion/README.md).

## Scope notes

The expensive full CPU command was not repeated after the final browser-profile
fix because the user explicitly stopped that rerun. The CPU model assertions
were verified at `735c960`; the affected Compose/browser correction was tested
at final revision `4b2d425` with the targeted browser and configuration checks.
This preserves exact tested revisions instead of implying one combined run.
WebKit was unavailable and remains optional/unclaimed. Generated audio,
weights, secrets, and disposable Compose state are excluded from Git.
