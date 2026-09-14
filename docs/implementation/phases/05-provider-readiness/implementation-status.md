# Phase 05 implementation status

- State: complete
- Completed: 2026-09-14
- Source branch: `phase-5-provider-readiness`
- Integrated test source: `d40fccc` (rebased on `origin/main` at `359eb89`)
- Scope: provider readiness, capability truthfulness, route isolation and mock regression; not release certification or broad real-model quality validation

## Implemented behavior

The API returns a typed capability matrix whose entries carry `supported`,
`unsupported`, or `unknown` state, evidence and limits. New version provenance
stores the matrix as JSON-compatible data; historical provenance without it
remains readable. Legacy boolean capability fields remain nullable when behavior
is unknown. The composer filters provider-specific lyrics modes, languages and
operations, blocks incompatible saved choices, disables ineffective duration
controls, and displays provider readiness and capability evidence.

The provider boundary includes progress and cooperative cancellation callbacks,
typed provider failures and validated result metadata. Mock output remains
functional through the durable queue. The YuE2 route is isolated to its own
worker and queue, and does not fall back to mock output on missing requirements
or runtime failures. Configuration tests cover independent lyrics/music
providers, pinned model identity, runtime selection and incompatible devices.

## Verification

All Phase 05 implementation checks passed. The VM run used a unique project and
cleaned its containers, network and volumes after completion. Exact outputs and
environment details are in the [Phase 05 evidence](../../evidence/05/2026-09-14-provider-readiness/README.md).

- Local Python unit tests: 173 passed; 5 optional NumPy-dependent tests skipped.
- Local frontend build and unit tests: TypeScript/Vite build passed; 3 Vitest tests passed.
- Docker test-image unit suite: 172 passed; 6 expected skips (Git-only checkout and optional NumPy tests).
- Real PostgreSQL/RabbitMQ integration: 49 passed, including provider-route and packaging checks.
- API-served browser suite: 34 passed and 22 intentional skips across desktop, mobile, small and narrow widths. Capability and missing-project checks passed at every width; the desktop library workflow passed.
- Queued work survived API restart, completed after the worker resumed, and persisted a playable artifact. The mock smoke decoded to non-silent 44.1 kHz stereo WAV audio at the requested five-second duration.
- Mock-only, YuE2-only and combined Compose service profiles all resolved as intended.
- Prior D03 evidence records one real YuE2 application result, startup/no-fallback checks and API playback/seek. The fresh Phase 05 run did not perform new model inference.

See the [model integration boundary](../../../model-integration.md) for the
capability-by-capability evidence and limits.

## Capability result

| Provider | Verified behavior | Unsupported behavior | Unknown behavior |
| --- | --- | --- | --- |
| Mock | Supplied lyric preservation; scripted demo lyric modes; validated non-silent audio; requested duration; deterministic output for the same seed | Sung vocals, exact lyrics singing, language/music-control fidelity, reference-audio conditioning, editing and continuation | None claimed for the mock contract |
| YuE2 | Supplied English lyrics reach the adapter; validated technical WAV output; durable queue/API transport on the separately recorded D03 result | Separate lyric generation, requested duration control, reference-audio conditioning, editing and continuation | Instrumental-only output, vocal behavior, exact lyric adherence, audio-language fidelity, style-control fidelity and cross-runtime seed reproducibility |

A valid WAV establishes transport and technical audio properties only. YuE2's
unknown semantic behavior remains unknown; no UI label or acceptance statement
promotes it to verified support.

## Remaining work outside Phase 05

Phase 06 release verification remains open. Part 2 D04/D05 deployment validation
and operational handoff remain separate. A fresh real-model inference was not
part of the Phase 05 regression gate, and the optional YuE2 CPU-inference smoke
was not run here; neither is required to establish the mock regression or the
capability boundary recorded above.
