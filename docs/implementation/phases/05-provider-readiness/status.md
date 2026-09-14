# Phase 05 status

- State: in_progress
- Started: 2026-09-14
- Last updated: 2026-09-14
- Completed: not completed
- Current focus: capability contract, UI behavior, provider configuration, and regression evidence

## Completed work

The typed capability matrix now separates verified support, known gaps, and
unknown behavior for the mock and pinned YuE2 provider revisions. The API exposes
that matrix and includes it in new version provenance while accepting historical
snapshots without the field. The composer uses provider capabilities to choose
lyrics modes/languages and operations, blocks incompatible saved drafts, disables
unsupported duration control, and displays readiness, provenance and warnings.
Provider progress/cancellation and mock output metadata have conformance tests;
configuration tests cover independent lyrics/music choices and invalid YuE2
combinations. See [model integration](../../../model-integration.md).

Part 2 selected `m-a-p/YuE2-3B`; D03 has since integrated the adapter, separate
GPU worker image, real queue, startup checks and provenance. One durable English
user-lyrics job was retrieved and played through the API. This is narrow transport
and technical-audio evidence only; semantic music capabilities remain unknown or
unsupported as recorded in the matrix. See [D03 evidence](../../../deployment/evidence/2026-09-14-d03-review-corrections/README.md).

## Remaining work

Tasks 05-01 through 05-08 have implementation or prior D03 verification evidence.
Task 05-09 remains open for a fresh API-served capability browser run, resolved
Compose profile inspection, real-service route regression, and mock smoke against
this branch. Task 05-10 and final acceptance remain open until those checks pass.

## Blockers and decisions needed

No implementation decision is blocking. This checkout has no Docker/Compose
executable, so its real-service regression checks cannot run locally. The prior
documented Ubuntu1 D03 run already proves that a real result crossed the MuseForge
queue; the remaining gate is rerunning Phase 05 regression checks on a Docker
runner with this branch's changes.

## Latest verification

Local verification: 148 Python unit tests passed and one optional NumPy-dependent
test skipped; all three frontend unit tests and the TypeScript/Vite production
build passed. Provider configuration/API contract coverage passed in that suite.
The prior [D03 application evidence](../../../deployment/evidence/2026-09-14-d03-review-corrections/README.md)
contains integrated queue, startup, no-fallback, playback, and mock regression
results. The new matrix and UI browser regression still require a fresh run through
the API-served app. See [Phase 05 local evidence](../../evidence/05/2026-09-14-provider-readiness/README.md).

## Next action

05-09: run this branch's API-served browser, resolved Compose profile/queue, integration, and mock smoke checks on the documented Docker runner.
