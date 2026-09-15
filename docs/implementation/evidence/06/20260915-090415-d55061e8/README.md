# Phase 06 release verification — 2026-09-15

The final release gate passed on the authorized Linux VM `yolo1@10.42.0.42` at
source revision `7b017e05a7e63aeb185d14a97777834923d8f1b8`. Docker Engine was
29.8.0 and Compose was 5.5.1. The run used fresh, uniquely named Compose
projects and removed only those test-owned volumes after verification.

## Results

| Gate | Result |
| --- | --- |
| Frozen container unit suite | 172 passed, 6 expected skips |
| PostgreSQL/RabbitMQ integration | 49 passed |
| API-served Chromium browser | 34 passed, 22 intentional responsive/stateful skips |
| Frontend Vitest | 3 passed in 2 files |
| Release-runner safety tests | 3 passed in the pinned container test image |
| Recovery and interruption matrix | Passed: queued/API restart, publisher confirmation gap, dispatcher/broker restart, worker loss/lease recovery, full restart |
| Documented lifecycle | Passed: setup, start, migrate, seed, smoke, logs, artifact inspection, rebuild/update, stop/start |
| Persistence | Projects, settings, active versions, and audio hashes unchanged across update and stop/start |
| Workspace inspection | 9 viewport checks, 65 keyboard observations, reduced motion, native 200% zoom, long multilingual lyrics |
| Static release audit | `git diff --check`, tracked-file/build-context review, and documentation links passed |

The machine-readable record is [`release-summary.json`](release-summary.json).
It records container Python 3.13.15/Node 24.21.0, lock hashes, image pins,
sanitized configuration, and exact migration head `0004_worker_runtime`.
Recovery observations are in [`recovery-gate/`](recovery-gate/), including
publisher, broker, dispatcher, worker-loss, restart, and workspace inspection
records.

The visual run recorded the documented manual-copy fallback because the
internal Compose hostname is not a secure browser context; the existing browser
suite separately covers clipboard failure handling. WebKit was not installed in
the release image and no WebKit claim is made.

## Commands

The exact release command was:

```bash
bash scripts/test.sh release
```

The Docker-free runner safety cases are recorded in
[`release-runner-tests.log`](release-runner-tests.log); they cover explicit
project ownership, failure-output retention, and persistence mutation checks.

The normal lifecycle portion also invoked `setup.sh`, `start.sh mock`,
`migrate.sh`, `seed-demo.sh`, `smoke.sh mock`, `logs.sh`, `artifact-gc.sh`,
`stop.sh`, a rebuild/update, and a restart. No weights, credentials, or
generated media entered the checkout or build context.

## Capability and deployment boundary

This is Part 1 mock release evidence. The CPU mock emits validated deterministic
44.1 kHz stereo WAV and does not sing lyrics or semantically implement musical
controls. Existing YuE2 evidence remains a narrow English technical route and
does not establish lyric adherence, instrumental/vocal behavior, language or
style fidelity, duration control, or perceptual quality. Part 2 D04/D05 host
resource, real-browser, backup/restore, rollback, and operations validation
remain open.
