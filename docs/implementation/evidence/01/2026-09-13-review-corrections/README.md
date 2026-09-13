# Phase 01 review corrections

- Recorded: 2026-09-13T12:21:11Z
- Branch: `fix/phase-1-review`, created from `main` at `7d75c57`.
- Changes are the three focused commits on this branch, identified by [source checksums](source-sha256.txt).
- Runtime: existing `Ubuntu1` WSL2 distribution; Linux amd64 Docker Engine 29.8.0, Compose 5.5.1. No host runtime installation was needed.
- Final isolated integration project: `museforge-foundation-test-b18dd27b582b`; its containers, network, and three test-owned volumes were removed by the runner.
- Pinned runtime/dependency versions and schema head `0001_foundation` are unchanged.

## Corrections

1. The dispatcher and worker broker probe now executes in a subprocess with the configured total timeout. A stalled connection, channel, declaration, or cleanup cannot hold the heartbeat loop indefinitely; timed-out children are killed and reaped. Child output is suppressed and errors expose only safe categories.
2. Celery consumer diagnostics for unknown messages, unknown tasks, invalid tasks, and decode errors replace bodies, headers, arguments, and exception/stack details with fixed event codes. Operational logs and existing message disposition remain intact.
3. `.gitattributes` pins shell scripts to LF. The current Windows working tree was normalized without changing global Git configuration (`core.autocrlf` remains `true`).

## Verification

Commands below ran from the repository through `wsl -d Ubuntu1 -- ...`.

| Check | Command / procedure | Result |
| --- | --- | --- |
| Setup | `bash scripts/setup.sh` | Created the absent ignored `.env`; existing Linux engine and Compose prerequisites passed. |
| Clean frozen stack | `bash scripts/test.sh integration` | Clean pinned image builds and package/service boundaries passed. All 8 integration tests passed before and after ordinary down/up. |
| Real worker redaction | Integration runner publishes unknown protocol/task, invalid ETA, and malformed JSON with a unique sentinel | All four safe diagnostic codes appeared; sentinel absent from actual worker logs; worker remained healthy. |
| Persistence | Integration runner restarts its isolated stack | Workspace identity, durable broker message, and artifact marker survived. Actual PG18 data directory was `/var/lib/postgresql/18/docker`. |
| Final Python unit suite | `docker build --target test -f packaging/Dockerfile -t museforge-phase1-review-tests:20260913 .`, then `docker run --rm --network none museforge-phase1-review-tests:20260913 /app/.venv/bin/pytest tests/unit` | **63 passed, 1 skipped**, two unchanged upstream deprecation warnings. |
| Git and shell checks | Executed the four `tests/unit/test_scripts.py` functions through Python `runpy`, using temporary directories in WSL | All passed, including checkout with `core.autocrlf=true`, LF bytes, Linux Bash syntax, setup preservation, and explicit future-command failure. The Git-specific check is the sole skip in the image, which intentionally contains no Git. |
| Frontend | `docker build --target web-test -f packaging/Dockerfile -t museforge-phase1-review-web-test:20260913 .` | **2 Vitest tests passed**; the clean integration build also passed typecheck and production compilation. |

The integration run included 62 passing unit tests; a final test explicitly proving heartbeat-loop recovery after timeout was subsequently added and passed in the final 63-test unit run. Production code did not change after the successful integration run. The timeout tests stall the actual probe child entrypoint at each broker-operation boundary, verify it is reaped within the deadline allowance, then run another successful child. Separate tests verify unhealthy observations, bounded worker shutdown, and recovery to healthy observations.

The first integration attempt stopped because its invalid-keyword-arguments fixture reached Celery's execution handler instead of the consumer's invalid-task handler. Inspection of the pinned request parser identified invalid ETA as the correct input for that callback. The corrected fixture passed the complete subsequent run. The failed test stack was also cleaned up.

See [captured verification excerpts](verification.txt). Full local logs remain in ignored `test-results/phase1-review-integration.log` and `test-results/phase1-review-final-unit.log`.

## Limits and status

All checks required for these three corrections have run; none remain blocked. Browser viewport checks were not repeated because UI behavior did not change. The original [foundation evidence](../2026-09-13-foundation/README.md) is preserved as historical evidence. This correction does not claim Phase 02 generation, real providers, or Part 2 deployment. Changes remain on the local branch and have not been pushed.
