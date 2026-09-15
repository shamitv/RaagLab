# Phase 06 to-do

Updated: 2026-09-15. State: completed. See the [plan](plan.md),
[implementation report](implementation-status.md), and
[completion evidence](../../evidence/06/20260915-phase6-completion/README.md).

- [x] 06-01 Audit requirements and phase reports; correct unsupported claims.
- [x] 06-02 Complete the dated official-source dependency support/security review without unnecessary pin changes.
- [x] 06-03 Reproduce mock setup/start from a committed disposable checkout with isolated storage and loopback networking.
- [x] 06-04 Complete CPU/release runner corrections, executable regressions, normal CPU inference, provenance, deadlines, assertions, timing and cleanup safeguards.
  - [x] Persist one CPU/auto/CUDA device value, preserve auto fallback, and fail strict CUDA without mock substitution.
  - [x] Resolve 900-second warmup and 3,600-second inference deadlines with bounded outer allowances.
  - [x] Assert normal planning/token settings, no GPU allocation, exact lyrics, validated audio and matching checksums.
  - [x] Retain separate readiness/queue/generation timings, unique logs, bounded inspections and interruption evidence.
  - [x] Raise Ubuntu1 WSL memory to 40 GiB and validate the pinned external weights volume.
- [x] 06-05 Run real-provider browser playback/seek/download/refresh/reopen checks and retain Chromium evidence; WebKit recorded optional/unavailable.
- [x] 06-06 Verify saved audio across stop/start and ownership-checked cleanup, including interrupted-run cleanup.
- [x] 06-07 Refresh README, architecture, development, API, and model operating documentation.
- [x] 06-08 Publish the deployment handoff with service/storage/migration/routing/provider contracts and Part 2 ownership.
- [x] 06-09 Audit merged Part 2 D04/D05 reports within their recorded hardware and capability limits.
- [x] 06-10 Publish individual A01–A12 and 06-AC mappings, CPU measurements, logs, and screenshots.
- [x] 06-11 Certify the implementation and affected final browser correction; record the user-requested decision not to repeat the expensive CPU run.

The CPU model assertions were verified at `735c960`; the final browser Compose
profile correction and targeted browser check were verified at
`4b2d42599168925a4771dfc61901c4ad5456abd2`. No public API, schema, or migration
was changed.
