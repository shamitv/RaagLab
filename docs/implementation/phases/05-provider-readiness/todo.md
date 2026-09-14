# Phase 05 to-do

All items are application implementation work and remain unchecked. Planning
preparation is tracked in Phase 00. The separate Part 2 D03 record now contains a
YuE2 standalone image/model checkpoint; that checkpoint supplies evidence for
05-05/05-08 but does not check these tasks off.

- [ ] 05-01 Audit the capability schema against separate lyrics text, instrumental music, vocals, exact supplied-lyrics singing, audio conditioning/editing and continuation. Record supported/unsupported/unknown values with model/provider revisions and limits, never extrapolating one capability to another.
- [ ] 05-02 Complete shared provider conformance tests for normalization/validation, deterministic mock behavior, progress/cancellation, typed initialization/transient/resource/capability errors and result/audio metadata validation.
- [ ] 05-03 Finish API/UI capability-driven control handling, effective settings and readiness/staleness displays. Retain product options/limitations where useful; ensure selecting real mode cannot return demo output after a missing-adapter/weights/device failure.
- [ ] 05-04 Validate independent LYRICS_PROVIDER and MUSIC_PROVIDER configuration, model ID/revision/cache/device/precision/resource/duration/time/concurrency settings and snapshot provenance. Reject incompatible route/model changes for preserved retries explicitly.
- [ ] 05-05 Document the real-worker image/build contract and Compose override/profile selection: only selected provider queues can be consumed, API/mock images remain light, and a mock profile stays usable for diagnostics. Do not add a Dockerfile that pretends to run a nonexistent model.
- [ ] 05-06 Define a real-mode startup/configuration gate that fails clearly until an adapter/image is supplied. Validate mock-only, missing-real and accidental-mixed routing configurations through tests; audit resolved services rather than relying on profile names.
- [ ] 05-07 Write docs/model-integration.md with required adapter methods/errors, file publication protocol, capability examples, dependency isolation, safe single-inference/GPU process lifecycle, heartbeat/cancellation proof requirements and no-fallback policy.
- [ ] 05-08 Write the model-selection handoff to Part 2 D03: exact model/revision/license/access, supported controls/languages/lyrics conditioning, observed hardware/RAM/VRAM/disk, runtime compatibility and short queued inference evidence are required before activation.
- [ ] 05-09 Re-run affected provider, routing, lifecycle and API-served capability browser checks and the existing mock smoke; record which capabilities are mocked, unsupported and pending.
- [ ] 05-10 Synchronize phase/overall records and create implementation-status.md only when the mock, capability audit and model integration boundary are verified; explicitly report real adapter/inference as not implemented.

No task has been removed or moved. If scope changes, keep the original identifier, explain the change and link its destination. See [plan](plan.md) and [status](status.md).
