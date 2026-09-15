# Phase 05: Provider readiness

## Objective

The mock and integrated YuE2 routes expose evidence-backed capabilities and a stable provider boundary. The UI, API, and workers distinguish accepted request fields from verified model behavior and preserve route isolation and no-fallback behavior.

## Dependencies and entry criteria

Phase 04 persistence/recovery gates pass and the mock workflow remains usable. The narrow YuE2 D03 application gate also passed on the reference host: a durable English user-lyrics job ran through the real worker and its verified 48 kHz result was retrieved and played through the API. D03 proves transport, provenance, and technical audio handling; it does not prove lyric adherence, instrumental-only output, language fidelity, style-control fidelity, or duration control. Phase 05 audits and enforces those distinctions.

## Scope

Audit and complete provider types/capability handling, readiness lifecycle, independent lyrics/music configuration, provider-specific routing, and the real-worker build/configuration contract. Keep both the CPU mock and narrow YuE2 route usable while clearly identifying unverified model behavior.

## Work breakdown

1. **05-01** Add a typed evidence matrix for supplied/generated lyrics, instrumental output, vocals, exact-lyrics singing, language/style controls, duration, seed reproducibility, audio conditioning/editing, continuation, and validated audio output. Include state, evidence, and limits for mock and pinned YuE2 provider revisions.
2. **05-02** Complete shared provider conformance tests for normalization/validation, deterministic mock behavior, progress/cancellation, typed initialization/transient/resource/capability errors and result/audio metadata validation.
3. **05-03** Drive the composer from API capabilities: expose only supported lyrics modes/languages and operations, block saved drafts with unsupported choices, disable ineffective duration controls, and show provider/model/readiness plus capability evidence and warnings.
4. **05-04** Validate independent LYRICS_PROVIDER and MUSIC_PROVIDER configuration, model ID/revision/cache/device/precision/resource/duration/time/concurrency settings and snapshot provenance. Reject incompatible route/model changes for preserved retries explicitly.
5. **05-05** Document and verify the separate real-worker image/build contract and Compose profiles: API/mock images stay free of inference dependencies, only the selected route is consumed, and the mock profile remains available for diagnostics.
6. **05-06** Verify startup gates for invalid providers, missing YuE2 identity/weights/device, and intentionally combined diagnostic profiles. Check resolved services and queue bindings; no failure may return mock audio for a YuE2 job.
7. **05-07** Maintain docs/model-integration.md with actual adapter methods/errors, publication protocol, capability matrix, dependency isolation, GPU process lifecycle, heartbeat/cancellation proof, and no-fallback policy.
8. **05-08** Record the selected model/revisions/license/access, hardware and measured limits, runtime compatibility, and narrow queued inference evidence in the Part 2 handoff; keep unverified musical capabilities explicit.
9. **05-09** Re-run affected provider, routing, lifecycle and API-served capability browser checks and the existing mock smoke; record which capabilities are mocked, unsupported and pending.
10. **05-10** Synchronize phase/overall/deployment records and write implementation-status.md with implemented, tested, unsupported, unknown, and pending behavior. D03 real inference is implemented and narrowly verified; D04/D05 system validation and operations remain separate.

## Contracts and data changes

Keep existing request/envelope and database snapshot versions. Add the typed capability matrix to the capabilities API and new provenance snapshots. Historical immutable provenance without the matrix parses as an empty matrix; no database migration is required. Legacy capability booleans are nullable so `unknown` does not collapse into `unsupported`.

## Acceptance criteria

- **05-AC1:** Mock remains fully functional through the real queue and independent lyrics modes after provider-contract changes.
- **05-AC2:** Capabilities distinguish supported, unsupported, and unknown behavior for lyrics, instrumental output, vocals, exact lyric singing, style/language controls, audio operations, duration, and seed; UI/API behavior and labels match.
- **05-AC3:** Provider conformance and configuration/routing tests pass, including unknown adapter, missing real requirements and an incompatible worker receiving a request; none returns a successful mock substitute.
- **05-AC4:** API and CPU mock dependency/image sets remain free of heavyweight inference dependencies; YuE2 real-worker requirements are isolated and reproducibly documented without adding them to the API/mock image.
- **05-AC5:** Worker readiness/lifecycle, single active GPU inference intent, safe model initialization, heartbeat/cancellation and error propagation are specified and observable in mock tests without claiming a GPU was tested.
- **05-AC6:** The integrated YuE2 adapter/image follows the documented contracts; unverified lyric/vocal/language/editing behavior remains explicit rather than inferred from transport and audio-format acceptance.
- **05-AC7:** A12 and the mock regression smoke pass with evidence; the completion report distinguishes provider readiness from real inference.

## Verification

Run provider/configuration unit tests, real-service provider-route and capability API tests, the API-served capability browser test, and mock smoke. Inspect API/mock dependency sets and resolved mock/YuE2/combined Compose profiles. Compare every UI control with its capability state and request action. Save the matrix, source revision, and command results under `docs/implementation/evidence/05/<run-id>/`. The D03 model gate remains supporting real-inference evidence, not evidence of unverified semantics.

## Risks, assumptions, and deferred work

The full product target includes vocals and precise lyrics/audio operations that the
YuE2 standalone run does not prove. Part 2 must evaluate fit against actual
hardware and the application contract; a short successful song does not establish
exact lyric adherence, all languages, editable audio, or continuation. Do not let a
broad boolean such as supports_music hide unsupported options.

See the [master plan](../../master-plan.md), [requirement matrix](../../requirements-matrix.md), [status](status.md) and [to-do list](todo.md).
