# Phase 06 implementation status

- State: completed
- Implementation revision: `4b2d42599168925a4771dfc61901c4ad5456abd2`
- CPU model verification revision: `735c960d9a52b17023271e126b14a65bce2e01ed`
- Migration head: `0004_worker_runtime`
- Evidence: [completion package](../../evidence/06/20260915-phase6-completion/README.md)
- Dependency review: [2026-09-15 support/security review](../../dependency-review-2026-09-15.md)

## Delivered

Phase 06 completed the release runner and deployment verification work without
changing public APIs, product schemas, or migrations. Device selection now has a
single persisted value with explicit CPU/auto/CUDA propagation, automatic
fallback, and strict CUDA failure. Compose deadlines resolve to 900 seconds for
warmup and 3,600 seconds for inference, with queue/watchdog/restart/browser and
cleanup allowances. Normal assertions cover pinned provenance, CPU/torch-eager,
four threads, concurrency one, the 28 GiB limit, no GPU allocation, normal
planning/token settings, exact lyrics, validated nontruncated audio, and API
checksum persistence.

The runner records readiness, queue delay, generation timing, Docker resource
samples, unique command logs, interrupted output, version/lock/image metadata,
and migration/readiness results. Cleanup checks Compose ownership labels before
destructive actions, preserves external weights, terminates process groups, and
records failures after both Compose and temporary-worktree cleanup.

## Verification

- Python unit/compile checks: 191 tests passed; focused release/deployment
  regressions: 13 passed.
- Committed mock release: 42 outcomes passed, including PostgreSQL/RabbitMQ
  integration, frontend unit/build, API-served Chromium, recovery, lifecycle,
  persistence, and cleanup.
- Normal CPU YuE2: passed on a reference host that met the 32 GiB prerequisite,
  with external pinned weights, a 28 GiB worker limit, and four CPU threads. The accepted result has
  exact lyrics, `torch-eager` CPU provenance, normal settings, validated 48 kHz
  stereo audio, and identical audio SHA-256 before and after stop/start.
- Final browser correction: targeted API-served Chromium passed playback,
  seek, download checksum, refresh, and project reopening. The affected Compose
  profile resolved cleanly at the final revision.

The full CPU command was intentionally not repeated after the final browser
profile-only correction at the user's direction. The evidence package records
the CPU and final browser revisions separately and retains the interrupted
rerun's partial evidence. WebKit was optional and unavailable.
