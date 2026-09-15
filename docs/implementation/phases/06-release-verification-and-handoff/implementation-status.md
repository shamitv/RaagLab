# Phase 06 implementation status

- State: in_progress
- Completed: not yet
- Last verified implementation revision: `c7b2a87c55d1c80b2142c7bd179adff9290808ff`
- Tested migration head: `0004_worker_runtime`
- Evidence: [committed-revision mock run](../../evidence/06/20260915-104002-622828de/README.md); [blocked CPU preflight](../../evidence/06/20260915-cpu-gate-blocked/README.md)

## Delivered

`bash scripts/test.sh release` forwards revision/options to a runner that creates
a disposable detached checkout, generates fresh configuration, filters its child
environment, and runs isolated Compose projects. It records source revision,
lock hashes, image IDs/digests, runtime versions, migration/readiness, command
outcomes, persistence comparisons, and Compose cleanup results. Existing
integration/e2e commands remain available.

The recorded mock gate passed all 42 command outcomes, including real
PostgreSQL/RabbitMQ recovery, frontend checks, API-served Chromium, documented
setup/start/migration/seed/smoke/logs, artifact maintenance dry-run, and
rebuild/update plus stop/start persistence. Ten focused runner/deployment tests
passed separately on the candidate; these include executable runner checks and
source-based deployment checks.

The deployment scripts include CPU/CUDA/auto override selection.
`--real-cpu` invokes the added `--cpu --normal` verifier with a 32 GiB memory
preflight and 28 GiB worker limit. Durable-generation provenance/audio assertions,
resource sampling, and a stop/start checksum comparison are present. These paths
have not passed the required normal-mode CPU runtime gate.

Core operating/development/API/model documentation and the
[deployment handoff](../../../deployment-handoff.md) were refreshed. Merged
Part 2 D04/D05 reports are complete only for their recorded Ubuntu1 validation
and operations evidence.

## Corrections to completion claims — 2026-09-15

The earlier status said overlapping tasks were both complete and open and
described the CPU verifier as finished apart from host eligibility. The
[plan](plan.md) and [checklist](todo.md) now distinguish delivered code, passing
mock checks, unfinished verification, and the independent host blocker.

Remaining code/verification work includes:

- Align worker/verifier device configuration and explicit CPU fallback semantics;
  add behavioral tests for CPU, strict CUDA, auto selection, and persisted mode.
- Replace inherited 900/930-second inference/watchdog settings with the required
  consistent normal CPU budgets; assert normal token/planning settings.
- Wire the real CPU browser workflow into the gate, preserve separate readiness,
  queue, and generation timing, and finish bounded subprocess/network behavior.
- Validate cleanup resource ownership, retain interrupted command output, and
  include outer worktree cleanup in final status and regression coverage.
- Complete the dated dependency review and individual acceptance mapping. The
  current compact summary groups A01–A12 and links historical screenshots;
  final evidence must preserve the tested run's own referenced logs/screenshots.

These follow-ups remain necessary even after an eligible host is supplied.
The passing mock revision does not certify later implementation changes or the
final merged revision. No public API, schema, or migration changes were made.

## Runtime blocker and boundaries

CPU preflight ran on the selected VM and failed before model startup: 7.2 GiB
available versus 32 GiB required. The host has 10 GiB total RAM and lacks the
verified weights volume. Normal CPU generation, browser acceptance, measured
performance, and lifecycle preservation therefore remain unrun.

Chromium ran; optional WebKit was unavailable. The internal Compose hostname
uses the application's manual-copy fallback. Technical CPU generation, when
verified, will not establish lyric adherence, musical quality, exact duration,
broad YuE2 capabilities, or additional native host portability.
