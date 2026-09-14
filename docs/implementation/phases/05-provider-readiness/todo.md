# Phase 05 to-do

Tasks with implementation or prior D03 evidence are checked below. Final phase
closure waits for the fresh integrated checks tracked by 05-09. Planning
preparation is tracked in Phase 00.

- [x] 05-01 Audit provider capabilities independently for lyrics input/generation, instrumental music, vocals, exact supplied-lyrics singing, audio conditioning/editing/continuation, controls, duration, seed behavior and technical output; record evidence and limits for the mock and pinned YuE2 revision.
- [x] 05-02 Add provider conformance checks for normalization/validation, deterministic mock output, progress/cancellation, typed failures, and audio metadata/publication.
- [x] 05-03 Drive composer modes, language choices, operations, duration controls, saved-draft validation, readiness and warnings from API capabilities; preserve the no-fallback behavior.
- [x] 05-04 Cover independent lyrics/music provider settings, YuE2 identity/device/precision requirements, route selection and immutable provenance; retain existing retry route/model checks.
- [x] 05-05 Document and verify separate real-worker image/build and Compose selection; API/mock images remain free of inference dependencies and the mock profile remains usable.
- [x] 05-06 Verify startup failures for missing YuE2 identity/weights/device, provider routing and no-fallback behavior; D03 resolves mock/real/combined Compose configurations.
- [x] 05-07 Document the active adapter contract, errors, publication protocol, capability matrix, dependency isolation, supervised GPU lifecycle, heartbeat/cancellation, and no-fallback policy.
- [x] 05-08 Record model/revision/license/access, hardware and measured limits, runtime compatibility, and queued inference evidence in the Part 2 handoff.
- [ ] 05-09 Re-run affected provider, routing, lifecycle and API-served capability browser checks and the existing mock smoke; record which capabilities are mocked, unsupported and pending. Local unit/UI checks are recorded; the integrated runner is still required.
- [ ] 05-10 Synchronize phase/overall records and create implementation-status.md only after the mock, capability audit and model integration boundary are verified; distinguish the implemented narrow YuE2 inference route from unverified product behavior.

No task has been removed or moved. If scope changes, keep the original identifier, explain the change and link its destination. See [plan](plan.md) and [status](status.md).
