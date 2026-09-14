# Verification strategy and acceptance catalogue

- Date: 2026-09-14
- Current evidence: [planning verification](evidence/planning-verification.md), [Phase 01 implementation](evidence/01/2026-09-13-foundation/README.md), [Phase 04 projects and recovery](evidence/04/2026-09-14-projects-recovery/README.md)
- Status: Phases 01–04 are implemented and verified; Phase 05 provider readiness and Phase 06 release verification remain planned.

## Execution environments and evidence discipline

Unit tests exercise substantial validation, provider contracts and state rules. Integration tests require actual PostgreSQL 18, RabbitMQ and a separate worker through the packaged Compose network. Browser tests use the API-served built SPA; no route interception or eager Celery is evidence for the integrated flow. A Vite dev-server run is supplemental only. Mock mode never requires a GPU, weights, private token or paid service.

Use a unique Compose project and fixture namespace for integration/e2e fault tests. Do not kill or reset a user's ordinary library deployment. Test setup creates only test-owned data; destructive cleanup is restricted to that named test environment. Normal start/stop never deletes volumes. Validate `docker compose config` before running profiles/overrides, and assert resolved service names and routes rather than relying on profile assumptions. Docker's [profile guide](https://docs.docker.com/compose/how-tos/profiles/) explains why selecting one service does not activate every peer in a profile.

Create evidence under `docs/implementation/evidence/<phase>/<run-id>/` as meaningful summaries with commands, environment, revision, results and links. Keep verbose logs, traces/screenshots/audio in ignored test-output directories; preserve relevant reviewable evidence as small attachments or designated CI artifacts. Completion reports must link to accessible evidence and name tests that did not run. Never turn a missing Docker/browser environment into an all-green result.

## Phase 04 completed gate

Phase 04 passed on the user-authorized isolated runner at `yolo1@10.42.0.42` with Docker 29.8.0, Compose 5.5.1, Python 3.13.15, PostgreSQL 18.6, RabbitMQ 4.3.5, Node 24.21.0 and npm 11.19.0. Python unit tests had 102 passes and one expected Git-only skip; real-service integration had 42 passes, including upgrade from `0002_version_favorites` to `0003_workspace_settings`; the pinned frontend target passed build/typecheck and 3 unit tests. API-served Playwright ran 48 cases: 30 passed and 18 were intentionally skipped because shared stateful scenarios run once at desktop width. Playback, routing and responsive checks passed at 1440, 390, 360 and 320 px.

Separate uniquely named Compose runs proved confirmed-publish ambiguity/reclaim, dispatcher restart, broker outage recovery, whole-worker loss with a bounded second attempt, queued acceptance through API restart, and full Compose stop/start preserving projects, settings and playable artifacts. Evidence and test outputs are linked from the Phase 04 report. These tests use the mock provider; real-model inference/provider readiness and release certification remain Phase 05/06 work.

## Command interfaces

Phase 01 owns the initial script entry points; subsequent phases extend them. Phase 04 adds a real isolated end-to-end runner; full release certification still belongs to Phase 06.

| Command | Required behavior |
| --- | --- |
| `bash scripts/setup.sh` | Validate prerequisites, initialize absent local environment file without replacing existing settings, explain Linux-engine requirement |
| `docker compose --env-file .env --profile mock config` | Resolve default services, internal networking, persistent volumes and loopback binding |
| `docker compose --env-file .env --profile mock up -d --build` | Build UI-containing API and CPU worker; run controlled migration dependency; start DB/broker/dispatcher/mock worker |
| `bash scripts/start.sh mock` | Validated wrapper for that startup, readiness wait, clear local URL |
| `bash scripts/migrate.sh` | One controlled Alembic upgrade with advisory lock; no competing API startup migrations |
| `bash scripts/seed-demo.sh` | Idempotent original demo template/fixture metadata setup; no paid/gated asset |
| `bash scripts/logs.sh <job-id>` | Filter correlated logs without exposing lyrics/prompts/secrets |
| `bash scripts/smoke.sh mock` | Create fixture project/job, wait with a deadline, assert DB/provider path and decode/seek artifact; print IDs |
| `bash scripts/test.sh unit` | Run pytest domain/provider checks and frontend type/component checks with frozen dependencies |
| `bash scripts/test.sh integration` | Start/validate isolated real-service stack and run pytest integration cases |
| `bash scripts/test.sh e2e` | Build API SPA, start isolated stack and run Playwright/axe at the API origin |
| `python3 scripts/verify-phase4.py` | Run pinned Python/frontend/API-served browser checks plus isolated dispatch, worker, and volume-restart recovery evidence |
| `bash scripts/test.sh release` | Clean-build mock acceptance, integration/e2e suites and persistence smoke in an isolated project |
| `bash scripts/stop.sh` | Stop/remove containers while preserving data, broker and artifact volumes |

Wrappers must fail with nonzero exit status on a failed required assertion and use bounded waits, not arbitrary sleeps as success. Add a separate explicitly named reset command only if needed; ordinary start/stop/update cannot use `down --volumes`. A future real start command must fail if the selected adapter/image/configuration is absent.

## Part 1 acceptance tests

IDs A01–A12 correspond exactly to Part 1 section 13's numbered list. Planned test paths are stable obligations, subject to renaming with a documented mapping.

| ID | Planned evidence / scenario | Pass condition | Phase gates |
| --- | --- | --- | --- |
| A01 | `tests/integration/test_packaging.py`, clean-start log | Fresh checkout builds frozen images; DB/broker/migrate/API/dispatcher/mock worker start using documented command | 01, 06 |
| A02 | `test_static_hosting.py`, `tests/e2e/routing.spec.ts` | API serves built bundle; direct nested route refresh works; unknown API/missing asset return correct errors; entry/assets cache correctly | 01, 06 |
| A03 | `test_generation_pipeline.py`, `generation.spec.ts` | 202 returned promptly; real broker message reaches separate worker; PostgreSQL job/version exists; actual audio decodes with nonzero samples and plays | 02, 06 |
| A04 | `test_lyrics_preservation.py`, `lyrics.spec.ts` | Exact submitted Unicode/newlines/stanza labels survive job, version, retry and reopening; static/mock/user labels distinct | 02, 03, 04 |
| A05 | `test_persistence_restart.py`, `reopen.spec.ts` | Refresh and API/full-stack ordinary restart preserve jobs, draft revision, active selection, versions and playable artifacts | 02 basic, 04, 06 |
| A06 | `test_version_lineage.py`, `iterations.spec.ts` | Each refinement/variation has correct parent and new immutable content; selecting old versions retains newer history | 03, 04 |
| A07 | `test_idempotency.py`, `test_concurrent_completion.py` | Same key/payload same job; conflicting key 409; duplicate deliveries one result; concurrent completions unique numbers; stale selection stays selected | 02 basic, 04 |
| A08 | `test_dispatch_recovery.py`, `test_worker_recovery.py` | Kill after commit/before publish and after publish/before mark; recover accepted jobs; child/whole-worker loss bounded by leases/retry budget | 04 |
| A09 | `test_job_lifecycle.py`, `test_cancellation_races.py` | Failure/retry/queued and running cancellation/timeout have stable terminals and no discarded output version; prior versions remain available | 02 basic, 04 |
| A10 | `test_artifacts.py`, `player.spec.ts` | Byte-range 206 and 416/HEAD/media headers correct; browser seeking/download work; invalid IDs/traversal/symlinks rejected | 02, 03, 04 |
| A11 | `responsive.spec.ts`, `accessibility.spec.ts` | Required widths, long content and keyboard flow work without horizontal page scrolling; zoom/fixed-nav/manual checks recorded | 03, 04, 06 |
| A12 | `test_capabilities.py`, `capabilities.spec.ts` | Display actual media/versions; separate text/vocals/exact lyrics/audio edit capabilities; real errors cannot yield a mock success | 02 baseline, 05, 06 |

## Focused unit and provider checks

Test schema/canonical intent hashing without mutating lyrics, allowed state transitions, fenced finalization predicates, effective capability rejection, version activation decisions, request snapshot independence, safe filename/key construction, accurate WAV metadata and deterministic mock seeds. Use property/table-driven cases where boundaries matter. Avoid tests that merely mirror a CSS declaration or trivial getter.

Mock fault controls are test/environment configuration (success, typed failure, timeout, cooperative/uncooperative cancel, stage delays); never public query flags that arbitrary production requests can set. Use barriers/hooks inside test-owned worker configuration for deterministic races. Contract tests instantiate every available provider and check typed request/result/error behavior. A future real-provider suite is opt-in and must name model/revision/hardware separately.

## Recovery and consistency case detail

| Case | Injection and expected observation |
| --- | --- |
| Publication gap | Stop dispatcher; submit and assert job/outbox committed; restart; one result appears |
| Ambiguous publication | Interrupt dispatcher after broker confirmation before outbox update; reclaim/publish duplicate; assert one final version |
| Unclaimed published job | Simulate dropped delivery/consumer absence; visible wait and bounded re-dispatch or queue timeout |
| Duplicate and old messages | Send same envelope twice and a superseded dispatch sequence; no duplicate attempt ownership/result |
| Worker loss | Kill child and whole worker separately; expiry produces re-dispatch under attempt cap, then result or explicit failure |
| Stale computation | Pause attempt until its lease expires; complete a successor; unpause old attempt; old result cannot overwrite |
| Cancellation races | Barrier immediately before terminal commit; run cancellation-first and success-first orders; assert single terminal and correct artifact references |
| Concurrent completion | Two jobs on one project complete together; unique numbers and latest-submission/manual-selection rules hold |
| Retry budget | Inject transient errors then success; inject repeated errors/loss; bounded attempt count, durable backoff and final visible error |
| Queue/DB interruption | Broker restart retains persisted tasks; DB outage prevents unsafe success; dispatcher/worker resume from durable records |
| Artifact failures | Full disk/permission error/malformed WAV; no success. Crash after rename leaves reclaimable orphan; shared files survive GC |
| Browser/API interruption | Close/refresh/offline/restart while pending; retrieve authoritative job and recover unsent draft without double submit |
| Save conflicts | Two tabs with same base revision; second save receives 412 and preserves both local/server choices |
| Provider mismatch | Real route offered to mock worker, unsupported schema/options, missing adapter/device; explicit failure, no fallback |

Record IDs, dispatch sequences, attempt tokens (non-secret), terminal rows/version counts, artifact checksums and correlated log excerpts. Do not log user lyrics or prompts as routine evidence; use original dedicated test fixtures when exact text assertions are necessary.

## Browser and audio checks

Use Playwright Chromium at 1440×1000, 390×844, 360×800 and 320×740. Inspect 768, 1199, 1200 and 1600 px boundaries, 200% zoom/large text and reduced motion. At release include a WebKit smoke at mobile width to catch playback/seek differences when that browser is available; if unavailable, report it separately and keep any required agreed browser gate open. The release's required baseline is Chromium plus manual touch/keyboard emulation; no untested device claim.

Capture empty, ready, queued/running, complete, failed, cancelled and offline/reconnecting states. Cover long native-script lyrics, overlong brief, wrapped options, menu focus, named icons, clip/copy failure, history navigation and no autoplay. Axe supplements explicit contrast, focus, announcements and target-size inspection. A full AA conformance claim requires those broader checks, not merely a zero-issue scan.

Validate WAV headers and decode samples, measured frame-count duration/rate/channels, non-silence/RMS, file size and checksum; browser asserts `loadedmetadata`, advancing playback time, pause, seeks and download. Listen to the original short mock sample where tools allow and record the observation; if no listening capability is available, identify subjective audio quality as unverified. Do not infer that a valid file fulfills a semantic song brief.

## Phase closure and release audit

At each phase, run its focused checks and affected earlier checks; expand only for actual changes/risks. Record exact commands/outcomes/environment in its report. A completed phase cannot hide an unrun required container/browser test. Phase 06 reproduces A01–A12 and checks the complete requirement matrix, docs, secret/artifact exclusions, restart persistence and provider boundary from a clean configured checkout.

Part 2 owns real GPU/CPU inference, host access, resource measurements, model license/revision evidence and an isolated coordinated backup/restore. Part 1's release handoff must identify those as pending and supply the mock command, storage/migration/routing contracts and evidence needed to begin D00.
