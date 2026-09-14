# Phase 04 implementation report

- State: completed
- Completed: 2026-09-14
- Branch: `phase-4-projects-recovery`
- Baseline: `5f4147e`
- Tested implementation revision: `0b717d4` (subsequent changes in this report/evidence commit are documentation and test evidence only)
- Evidence: [projects and recovery acceptance](../../evidence/04/2026-09-14-projects-recovery/README.md)

## Delivered

All tasks 04-01–04-12 are complete. Projects are searchable, stably paginated, reopenable, duplicable, and conditionally archivable; archiving refuses active jobs. The completed-version library searches project titles/version labels, filters favorites/genre/language, and orders by recent completion by default. Duplicates get fresh project/version IDs and remapped parentage/active selection while sharing immutable audio references.

Workspace settings are revisioned in Postgres with the composer/player defaults documented in the API contract. Five original revision-1 templates apply only to the editable draft. Saves preserve IndexedDB edits per tab and their base revision; stale saves keep the local value available for Keep local, Use server, and Save copy. If IndexedDB is unavailable, the UI keeps edits in memory and explains that local recovery was not saved.

Explicit retry creates a new idempotent linked job while preserving the original immutable execution snapshot, provider route and exact lyrics checkpoint. The snapshot retains the original operation, so lyrics-only retries continue to reuse their source audio. Automatic retries remain bounded. Outbox claims, leases and fences recover confirmed-publication ambiguity and worker loss without duplicate final versions. Cancellation/completion and concurrent version allocation preserve a single terminal result and manual selection rules.

Artifact availability is reported without rewriting version content. The maintenance command inspects by default and applies deletion only after the 24-hour grace, no version reference, no live attempt, and a fresh locked reference check. Migration `0003_workspace_settings` adds revisioned settings and the recovery/library indexes without rewriting prior migrations. OpenAPI-derived TypeScript types, API/development/reliability docs, status tracking and this report are synchronized.

## Acceptance results

| Criterion | Result |
| --- | --- |
| 04-AC1 | Passed. API integration and browser flows verified projects, library search/filter/cursors, favorite/label, duplicate graph/audio reuse, archive conflict/restore, settings revisions, template draft application and persisted restart state. |
| 04-AC2 | Passed. Browser checks covered saved draft/version reopen, offline and two-tab stale-save choices, duplicate-safe reconnection and IndexedDB failure reporting with in-memory edit retention. Queued jobs and workspace state survived API and full Compose restarts. |
| 04-AC3 | Passed. Integration lineage checks verified parentage, previous/shared audio, lyrics-only reuse, concurrent unique numbering, latest submission and manual-selection protection. |
| 04-AC4 | Passed. Duplicate submissions/deliveries and confirmed publisher ambiguity created at most one version per logical job. Explicit retries were linked new jobs with preserved snapshot/provider/checkpoint; automatic retries exhausted within the configured bound. |
| 04-AC5 | Passed. Expired outbox claim and confirmed-publish ambiguity recovered; dispatcher and broker restarts recovered accepted work; a killed worker's expired lease produced a bounded second attempt and success; stale owners were fenced. |
| 04-AC6 | Passed. Queued/running cancellation, completion race, typed timeout/failure, retry exhaustion and terminal resource exhaustion produced stable outcomes without attaching discarded media. |
| 04-AC7 | Passed. Missing artifacts remain inspectable and show unavailable; dry-run/apply tests protect shared references and live attempts, enforce the 24-hour grace, and handle unsafe paths and permission failure. A full Compose stop/start preserved projects, settings and readable audio. |
| 04-AC8 | Passed. Real PostgreSQL/RabbitMQ/dispatcher/worker tests and API-served Chromium evidence cover the required persistence, artifact, retry/recovery and changed workspace flows using isolated test data. |

## Verification

The pinned Python unit target passed 102 tests with one expected skip for the Git checkout test, which runtime images intentionally omit. The real-service integration suite passed all 42 tests in 265.57 seconds, including the 0002-to-0003 migration upgrade. The pinned Node target passed production typecheck/build and 3 Vitest cases. API-served Playwright passed 30 of 48 cases; the 18 skipped cases are intentional repetitions of stateful flows at non-desktop widths. Playback, navigation and responsive layout checks passed at 1440, 390, 360 and 320 px.

Independent isolated service runs passed confirmed publisher ambiguity, dispatcher restart, broker outage/restart, whole-worker kill and lease recovery, API restart with queued work, full Compose stop/start while retaining named volumes, and the post-restart audio smoke check. Each test Compose project was uniquely named and cleaned only after its evidence was saved. See the [evidence README](../../evidence/04/2026-09-14-projects-recovery/README.md) for logs, JSON assertions, screenshots and tested source revisions.

## Boundaries

These gates exercise the original CPU mock provider. They do not certify a real model, real provider routing/readiness, semantic music controls, sung lyrics, WebKit, accessibility conformance beyond the recorded browser checks, deployment backup/restore, or release certification. Those remain Phase 05/06 work. All 12 task IDs and all eight acceptance criteria are closed in the [Phase 04 checklist](todo.md) and [status](status.md).
