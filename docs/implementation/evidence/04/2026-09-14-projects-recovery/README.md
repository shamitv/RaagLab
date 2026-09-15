# Phase 04 projects and recovery evidence

Phase 04 acceptance completed on 2026-09-14 using isolated Compose projects on the authorized Linux runner `<verification-host>`. Docker was 29.8.0 and Compose was 5.5.1. The pinned containers supplied Python 3.13.15, PostgreSQL 18.6, RabbitMQ 4.3.5, Node 24.21.0 and npm 11.19.0. The final implementation and verification harness is recorded in [source-revisions.txt](source-revisions.txt).

## Results

- [Python unit run](phase4-python-unit-0b717d4.log): 102 passed, one expected Git-only checkout check skipped because runtime images do not include Git, and two upstream deprecation warnings.
- [Real-service integration run](integration.txt): 42 passed in 265.57 seconds. It exercised HTTP/API, PostgreSQL, RabbitMQ, separate dispatcher and worker, project/library/settings, artifact maintenance, lineage and concurrency, failure/retry/cancellation and migration upgrade from `0002_version_favorites` to `0003_workspace_settings`.
- [Pinned frontend run](phase4-web-test-0b717d4.log): TypeScript check and Vite production build succeeded; Vitest had 3 passing tests.
- [API-served Playwright run](browser.txt): 30 passed and 18 intentional skips. Shared-state flows ran once at 1440 px; playback, routing and layout checks ran at 1440, 390, 360 and 320 px. There were no failing assertions.
- [Confirmed publisher ambiguity](ambiguous-confirm.json): RabbitMQ confirmed the first message, the expired `publishing` claim was reclaimed and published a second time, and the final record has one attempt and one version.
- [Dispatcher restart](dispatcher-restart.json), [broker outage/restart](broker-recovery.json), [whole-worker kill and lease recovery](worker-loss.json), and [full Compose restart](full-restart.json) all passed. Full restart retained five projects, workspace settings at revision 1, and every active audio artifact checked.
- [Queued job/API restart](queued-restart.json), [project/audio restart check](restart.json), and final [readiness response](readiness.json) passed. The isolated smoke produced a non-silent, decodable 5-second stereo WAV.

The two saved desktop screenshots show the [projects/library/settings/template flow](phase4-projects.png) and [two-tab draft conflict recovery](phase4-draft-recovery.png).

## Acceptance crosswalk

| Criterion | Evidence and result |
| --- | --- |
| 04-AC1 | `test_projects_library_settings.py` and the desktop Playwright lifecycle flow cover stable project/library search and cursors, filters, favorite/label, duplicate parent remapping/shared audio, archive conflict/restore, settings revision conflicts, and template application without auto-generation. Full restart preserves projects/settings. |
| 04-AC2 | `phase4.spec.ts` covers Save/reopen, offline edits, two-tab stale `If-Match`, Keep local/Use server/Save copy, and IndexedDB failure with in-memory retention. `queued-restart.json` and `full-restart.json` prove accepted work and saved workspace state survive service restarts. |
| 04-AC3 | `test_version_lineage.py` and `test_generation_pipeline.py` cover parentage, lyrics-only audio reuse, manual selection, duplicate delivery, simultaneous version numbering and latest-submission activation. |
| 04-AC4 | Generation integration checks prove idempotent submissions and duplicate delivery produce one version. The retry integration and browser checks prove a new linked job preserves the original snapshot, provider route and lyrics checkpoint; retries remain bounded and cannot chain. |
| 04-AC5 | `ambiguous-confirm.json`, `dispatcher-restart.json`, `broker-recovery.json` and `worker-loss.json` prove confirm ambiguity, claim reclamation, broker/dispatcher restart, committed queued work and lease-bounded whole-worker recovery. |
| 04-AC6 | Integration checks cover queued/running cancellation, cancellation/completion race, typed timeout/failure, retry exhaustion and terminal resource exhaustion. Late/stale writes are rejected by fence checks; discarded jobs have no attached result. |
| 04-AC7 | Artifact tests cover missing-object availability, shared-reference protection, live-attempt protection, 24-hour retirement/apply behavior, unsafe paths and permission failures. `full-restart.json` confirms named volumes kept project/settings/media state. |
| 04-AC8 | Real PostgreSQL 18.6/RabbitMQ 4.3.5 integration with separate dispatcher/workers and API-served Chromium covers A05–A10 and changed workspace flows at the documented viewports. Browser tooling ran in a test-only image, outside API/worker runtime images. |

The Playwright skips are the documented desktop-only repetitions of the stateful settings, conflict, retry, clipboard/offline-save and cancellation scenarios; corresponding responsive routing, playback and layout tests passed at the other widths. This is Chromium evidence, not WebKit or full Phase 06 accessibility/release certification.

## Reproduction

On a Linux Docker host with the pinned images available, run `python3 scripts/verify-phase4.py`. It creates a uniquely named test project and removes only that project's containers and volumes after writing `test-results/`. The exact browser/service pass was also run with `PHASE4_BROWSER_ONLY=1`; the final recovery harness, including publisher-confirm ambiguity, was rerun at the final code revision with `PHASE4_BROWSER_ONLY=1 PHASE4_RECOVERY_ONLY=1`. The Python and frontend logs linked above came from their pinned image targets.

The integration log is from source revision `15e4b03`. Git comparison confirmed `src/museforge` and `migrations` are unchanged between that integration-tested revision and the final source revision; the later changes in those ranges were browser/verifier code. Browser application sources were unchanged from `9be2e0d` to the final source revision. Real-provider inference and deployment certification are explicitly deferred to Phases 05 and 06.
