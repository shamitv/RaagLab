# Requirement traceability matrix

- Baseline: [Part 1](../prompts/01-portable-application.md) and [design](../../design.md)
- State: Phases 01–06 passed for Part 1; Part 2 D04/D05 remain. See [Phase 06 evidence](evidence/06/20260915-090415-d55061e8/README.md), [Phase 05 evidence](evidence/05/2026-09-14-provider-readiness/README.md), [Phase 04 evidence](evidence/04/2026-09-14-projects-recovery/README.md) for project/library/settings, save recovery, retry/dispatch/worker recovery, artifact safety and restart acceptance; [Phase 03 evidence](evidence/03/2026-09-13-workspace/README.md) records responsive workspace checks, and [Phase 02 evidence](evidence/02/2026-09-13-mock-end-to-end/README.md) records baseline generation, lyric and playback acceptance.
- Evidence catalogue: [verification strategy](verification-strategy.md); A01–A12 match the prompt's numbered acceptance checks
- Phase links and dependencies: [master plan](master-plan.md)

## Part 1 requirements

| ID / source | Required scope | Implementation owner | Acceptance / evidence obligation |
| --- | --- | --- | --- |
| P01 / section 1 | Audit actual repo/instructions; inspect design and both images; preserve references; no model inference from folder name | 00 | Planning audit, reference hashes, explicit model deferral |
| P02 / section 2 | API-served static UI, PostgreSQL, durable broker, dispatcher, separate worker, storage boundaries, portable monorepo | 00 decisions, 01 foundation, 02 full path | A01–A03; resolved Compose, image boundaries and job correlation |
| P03 / section 2 | Supported compatible versions, pins/locks, no heavy API/mock dependencies or second result store | 00 baseline, 01 locks, 06 release check | Dependency evidence; frozen builds; dependency/image inspection |
| P04 / section 3 | Master/status/ADR plus concrete plan/status/to-do per phase; stable IDs and honest closure reports | 00 then every phase | Structural/link/content audit; completion reports only after gates |
| P05 / section 4 | Clear code responsibility layout and ignored weights/audio/secrets/cache/data | 01, completed 06 | Source tree, build contexts and tracked-file audit |
| P06 / section 5 | Early real-service UI -> DB/outbox -> broker -> worker -> playable mock audio | 02 | A03; demonstrable checkpoint with browser trace and DB/media assertions |
| P07 / section 5 | Independent lyrics/music providers; exact user lyrics; static/mock labels; original deterministic audio/provenance | 02 | A04/A12; provider tests, original-fixture manifest and decoded output |
| P08 / section 5 | Mock delay/failure/timeout/cancel controls and project isolation | 02, hardened 04 | A07/A09; dedicated multi-project jobs and fault controls |
| P09 / section 6 | Versioned typed API, input/capability validation, required routes, OpenAPI/types, 202 response and polling | 01–04 | A02–A04/A09; contract tests and prompt-response timing |
| P10 / section 6 | Persistent scoped idempotency, conflict detection, immutable normalized snapshots, linked user retry | 02 baseline, 04 retry/races | A04/A07/A09; request/retry snapshot assertions |
| P11 / section 6 | Versioned JSON queue with IDs/timestamp/provider route; no binary/weights/executable serialization | 02 | Envelope/schema tests, worker route inspection, A03/A12 |
| P12 / section 6 | API build stage/static hosting, relative URLs, SPA exclusion, cache/ranges/traversal, same-origin/CORS | 01 hosting, 02 artifacts, 03 player | A02/A10; nested route, missing API/asset, range/security tests |
| P13 / section 7 | Relational entities, migrations, FKs/UUID/UTC/indexes/JSONB, controlled migration command | 00 schema, 01 migration, 02/04 extensions | Real PostgreSQL schema/constraint/migration checks; A01/A07 |
| P14 / section 7 | Immutable version lineage/selection, concurrent numbering, single result per job, honest duration/structure | 02 foundations, 03 iteration, 04 races | A05–A07/A12; selection barrier and concurrent completion tests |
| P15 / section 7 | Immediate durable jobs/results; Save semantics, local draft/base revision, server conflict handling | 02 persistence, 03 draft, 04 save/recovery | A05; multi-tab 412/offline/reopen checks |
| P16 / section 7 | Atomic artifact publication, orphan/missing recovery, shared-reference retention and lyrics-only reuse disclosure | 02 publication, 03 lyrics edits, 04 GC | A06/A10/A12; file/DB crash and shared-object tests |
| P17 / section 8 | Durable dispatch/confirms/retries/reconciliation; claim/lease/heartbeat/fence; framework ack semantics | 00 decision, 02 base, 04 fault suite | A07–A09; transaction-gap, worker-loss and stale-attempt tests |
| P18 / section 8 | Typed bounded retries/OOM failures, routing, all job states, cancellation race/timeouts/restarts | 02 base, 04 full | A08/A09/A12; stable terminal and bounded recovery evidence |
| P19 / section 8 | Correlated private-by-default logs, worker readiness, API/model startup separation, safe GPU lifecycle boundary | 02, 05; GPU execution Part 2 D03 | A03/A12; heartbeat/log checks and explicit real-model gate |
| P20 / section 9 | Composer, player, lyrics, iteration, structure, history; all exposed actions function | 02 basic, 03 full workspace, 04 organization | A03/A06/A10/A11; UI action audit |
| P21 / section 9 | Create/Library/Projects/Settings/Templates; favorite/rename/duplicate/archive, save/reopen | 03 metadata, 04 complete flows | A05/A06/A11; route/navigation/library/preferences tests |
| P22 / section 9 | All job/network states, exact lyrics/non-Latin text, no fake waveform/progress/semantics/autoplay | 02–04 | A04/A09/A11/A12; state screenshots and playback assertions |
| P23 / section 9 | 1440/390/320–360 responsive layouts, accessibility, no horizontal page scroll; document tradeoffs | 00 UI decision, 03, 04 changed flows | A11; viewport, keyboard, contrast, zoom, reduced-motion evidence |
| P24 / sections 9–10 | Omit unavailable collaboration/billing/notifications/accounts; distinct text/instrumental/vocal/exact-lyrics/edit capabilities | 00 scope, 03 UI, 05 audit | A12; full control-to-capability/action mapping |
| P25 / section 10 | Typed provider lifecycle/errors/normalization/results; independent config, limits/revisions/storage/device/concurrency | 00 contracts, 02 mock, 05 boundary | Provider contract tests, config validation, A12 |
| P26 / section 10 | Part 1 deferred model selection and a concrete adapter to Part 2; D03 now supplies a narrow YuE2 adapter, with dependencies isolated and no silent fallback | 05 handoff; Part 2 D03 | A12; missing-real-mode error test; unsupported and unknown capabilities remain explicit |
| P27 / section 11 | Reproducible API/mock images, deliberate profiles/overrides, persistent volumes, health/migrations/shutdown | 01, 05 real boundary, 06 docs | A01/A05; resolved-service assertions and normal restart |
| P28 / section 11 | Safe environment examples, configurable paths/ports/providers, loopback/internal network, no host-path dependency | 01, 06 audit; target config Part 2 | Compose/source/config checks; A01/A02 |
| P29 / section 11 | Setup/start/stop/migration/seed/log/smoke/test entry points, separate reset, local security boundary | 01 skeleton, 02 smoke, 04 maintenance, 06 runbook | Reproduction of documented commands; no-volume-delete stop |
| P30 / section 12 | Seven dependency-ordered phases; Phase 02 integrated checkpoint before polish/model | 00 scheduling, 02 demo | Phase plan graph and Phase 02 evidence |
| P31 / section 13 | Twelve acceptance checks with real services; meaningful tests; GPU checks opt-in; blocked tests reported | 01–06 | A01–A12 individually recorded; never substitute mock transport or unit-only evidence |
| P32 / section 14 | Source/config/migrations/fixtures/tests/docs and current reports; tested start command, implemented/tested/mock/pending split | 01–06 deliverables, 06 handoff | Final clean-checkout audit and Part 2 handoff; planning run delivers plans only |

## Numbered acceptance ownership

| Prompt section 13 item | Primary gate | Required supporting evidence |
| --- | --- | --- |
| 1 / A01 | 01, repeated 06 | Frozen clean build/start and controlled migrations |
| 2 / A02 | 01, repeated 06 | Packaged SPA routing/assets/errors/caching |
| 3 / A03 | 02, repeated 06 | Real broker/worker/DB path and decoded playable media |
| 4 / A04 | 02–04 | Exact lyrics and distinguishable source modes |
| 5 / A05 | 04, repeated 06 | Browser/API/full-stack restart and selection/history persistence |
| 6 / A06 | 03–04 | New immutable versions, correct parents, old-version selection |
| 7 / A07 | 04 | Submission/delivery duplicates and concurrent version uniqueness |
| 8 / A08 | 04 | Unpublished accepted job and worker-loss bounded recovery |
| 9 / A09 | 04 | Failure/retry/cancellation/timeout race outcomes |
| 10 / A10 | 02–04 | Range playback, safe artifact lookup and download |
| 11 / A11 | 03–04, repeated 06 | Responsive/keyboard/zoom/no-overflow core workflow |
| 12 / A12 | 05, repeated 06 | Actual metadata, honest capabilities, no real-to-mock fallback |

## Design coverage and scope decisions

| Design section | Planned realization | Owner / acceptance |
| --- | --- | --- |
| 1–3 Product intent/core/principles | Creation-first, blue hierarchy, audio playback, non-destructive versioning | 02–04; A03/A06/A11 |
| 4 Information architecture | Create/Library/Projects/Settings/Templates and history; omit collaboration per Part 1 explicit deferral | 03–04; navigation/action tests |
| 5 Responsive layout | Desktop rail/columns, mobile safe bottom nav, preview-first reading order; documented 1440 px dimension adjustment | 03; A11 |
| 6 Visual system | Specified colors/type/spacing/radii, outline icons, contrast-tested primary actions, optional ambient art | 03; visual/manual accessibility evidence |
| 7 Brand/brief/chips/selects/advanced/generate | All reference choices, 500-code-point validation, lyrics mode editor, honest capability controls | 02–03; A04/A11/A12 |
| 7 Player/lyrics/structure | Actual audio/metadata, accessible seek, playback collection, copy/edit, bounded estimated structure | 02–03; A04/A10/A12 |
| 7 Iterate/actions/history | Apply/regenerate/refine/mood/instrument/variation actions, dynamic version count and atomic selection | 03–04; A06/A07 |
| 8 States/save/version behavior | Empty/ready/queued/running/partial when supported/failed/cancelled/offline; local drafts and conditional server save | 02–04; A05/A09 |
| 9 Accessibility | Contrast/targets/focus/names/chip semantics/announcements/non-color cues/reduced-motion/200% zoom | 03–04; A11 and manual checks |
| 10 Content | Stable creative labels, native scripts, original varied examples, explicit demo limitations | 02–03, audited 05; A04/A12 |
| 11 Component hierarchy | Shared AppShell/Composer/Result components, single audio state, responsive semantic reading order | 01 shell, 03 complete; A11 |
| 12 Data model | Server-backed superset with immutable snapshots, artifacts, lineage, jobs/revisions/selection safeguards | 00 design, 01–04 implementation; A05–A07 |
| 13 Acceptance | All desktop/mobile controls/choices, playback/favorite/navigation, iteration/history, long content and progressive disclosure | 03–04, release 06; A06/A10/A11/A12; collaboration explicitly deferred |
| 14 Scope note | Stereo demo audio and versioned iteration; no invented DAW stems or native multitrack notation | 00 boundary, 05 capability audit |

## Part 2 continuity

The companion prompt is a boundary reference, not a request to deploy during this run. Part 1 Phase 06 hands off to D00 inventory/plan, D01 host preparation, D02 verified target mock deployment, D03 model/adapter/real-worker activation, D04 real workflow/recovery/resource validation, and D05 runbook/manifest/isolated restore/portability evidence. Unmet vocals/exact lyrics/language/audio-edit capabilities stay explicit product targets; a narrower real model cannot silently redefine completion.
