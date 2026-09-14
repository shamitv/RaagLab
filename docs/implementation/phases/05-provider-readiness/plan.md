# Phase 05: Provider readiness

## Objective

The working mock product exposes truthful capabilities and a stable integration boundary so Part 2 can add a selected local music model without redesigning the UI, API, persistence or job transport.

## Dependencies and entry criteria

Phase 04 persistence/recovery gates pass and the current mock workflow remains usable. YuE2-3B is now selected only for the separate Part 2 standalone checkpoint; it is not an active application provider. Read the Part 2 deployment record as a handoff input, not as Phase 05 completion.

## Scope

Audit and complete provider types/capability handling, model/readiness lifecycle contract, independent lyrics/music configuration, provider-specific routing and the real-worker build/configuration contract. The deliverable remains an executable mock provider plus documented adapter/image integration requirements; actual application real inference remains Part 2 D03.

## Work breakdown

1. **05-01** Audit the capability schema against separate lyrics text, instrumental music, vocals, exact supplied-lyrics singing, audio conditioning/editing and continuation. Record supported/unsupported/unknown values with model/provider revisions and limits, never extrapolating one capability to another.
2. **05-02** Complete shared provider conformance tests for normalization/validation, deterministic mock behavior, progress/cancellation, typed initialization/transient/resource/capability errors and result/audio metadata validation.
3. **05-03** Finish API/UI capability-driven control handling, effective settings and readiness/staleness displays. Retain product options/limitations where useful; ensure selecting real mode cannot return demo output after a missing-adapter/weights/device failure.
4. **05-04** Validate independent LYRICS_PROVIDER and MUSIC_PROVIDER configuration, model ID/revision/cache/device/precision/resource/duration/time/concurrency settings and snapshot provenance. Reject incompatible route/model changes for preserved retries explicitly.
5. **05-05** Document the real-worker image/build contract and Compose override/profile selection, incorporating the isolated YuE2 image as a Part 2 reference: only selected provider queues can be consumed, API/mock images remain light, and a mock profile stays usable for diagnostics.
6. **05-06** Define a real-mode startup/configuration gate that fails clearly until an adapter/image is supplied. Validate mock-only, missing-real and accidental-mixed routing configurations through tests; audit resolved services rather than relying on profile names.
7. **05-07** Write docs/model-integration.md with required adapter methods/errors, file publication protocol, capability examples, dependency isolation, safe single-inference/GPU process lifecycle, heartbeat/cancellation proof requirements and no-fallback policy.
8. **05-08** Write the model-selection handoff to Part 2 D03: use the YuE2 standalone record for exact model/revision/license/access, observed hardware/RAM/VRAM/disk, runtime compatibility and short inference evidence, while keeping supported controls and application activation open.
9. **05-09** Re-run affected provider, routing, lifecycle and API-served capability browser checks and the existing mock smoke; record which capabilities are mocked, unsupported and pending.
10. **05-10** Synchronize phase/overall records and create implementation-status.md only when the mock, capability audit and model integration boundary are verified; explicitly report real adapter/inference as not implemented.

## Contracts and data changes

Freeze or deliberately version the provider/envelope/request contracts from ../../contracts.md. Persist model identity/revision when known, measured result metadata and effective capability provenance. Minor additive metadata is allowed with schema compatibility tests; breaking request/envelope changes require migration and version handling. The real adapter is intentionally absent, so the failure gate is real behavior to test rather than a placeholder returning fake audio.

## Acceptance criteria

- **05-AC1:** Mock remains fully functional through the real queue and independent lyrics modes after provider-contract changes.
- **05-AC2:** Capabilities distinguish all five product abilities and unsupported controls have explicit UI/API behavior; actual metadata and demo labels are accurate.
- **05-AC3:** Provider conformance and configuration/routing tests pass, including unknown adapter, missing real requirements and an incompatible worker receiving a request; none returns a successful mock substitute.
- **05-AC4:** API and CPU mock dependency/image sets remain free of heavyweight inference dependencies; YuE2 real-worker requirements are isolated and reproducibly documented without adding them to the API/mock image.
- **05-AC5:** Worker readiness/lifecycle, single active GPU inference intent, safe model initialization, heartbeat/cancellation and error propagation are specified and observable in mock tests without claiming a GPU was tested.
- **05-AC6:** Part 2 can implement its concrete adapter/image using the documented contracts; YuE2 is a selected test model, while exact-lyrics/vocal/language/editing targets and application activation remain explicit.
- **05-AC7:** A12 and the mock regression smoke pass with evidence; the completion report distinguishes provider readiness from real inference.

## Verification

Planned: bash scripts/test.sh unit with provider conformance/configuration/capability cases; bash scripts/test.sh integration for test_capabilities.py and queue-route/schema/missing-real tests; bash scripts/test.sh e2e with capabilities.spec.ts; bash scripts/smoke.sh mock. Inspect API/mock installed dependency lists and resolved mock/missing-real configurations. Compare every exposed control with its capability/action and evidence. Save the capability matrix and command results under docs/implementation/evidence/05/<run-id>/. The standalone YuE2 GPU/model run is recorded under docs/deployment; it does not replace these application checks.

## Risks, assumptions, and deferred work

The full product target includes vocals and precise lyrics/audio operations that the
YuE2 standalone run does not prove. Part 2 must evaluate fit against actual
hardware and the application contract; a short successful song does not establish
exact lyric adherence, all languages, editable audio, or continuation. Do not let a
broad boolean such as supports_music hide unsupported options.

See the [master plan](../../master-plan.md), [requirement matrix](../../requirements-matrix.md), [status](status.md) and [to-do list](todo.md).
