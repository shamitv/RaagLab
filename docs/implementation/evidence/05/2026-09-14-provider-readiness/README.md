# Phase 05 provider-readiness verification

Date: 2026-09-14. Branch: `phase-5-provider-readiness`. The integrated run used
source commit `d40fccc` after rebasing on `origin/main` (`359eb89`, YuE2
CUDA-first/CPU-fallback support). Docker runs used the configured Linux VM with
Docker Engine 29.8.0 and Compose 5.5.1. All test services used the isolated
Compose project `museforge-phase2-test-phase5-ad6105be2a15`; the VM's unrelated
`survey_app` containers were left running and untouched.

## Results

| Gate | Result |
| --- | --- |
| Local Python unit suite | 173 passed, 5 optional NumPy-dependent skips |
| Local frontend | TypeScript/Vite build passed; 3 Vitest tests passed |
| Docker test-image unit suite | 172 passed, 6 expected skips (Git-only checkout test and optional NumPy tests) |
| PostgreSQL/RabbitMQ integration | 49 passed in 270.92 seconds |
| API-served Playwright | 34 passed, 22 intentional skips across desktop, mobile, small and narrow projects |
| Queued API restart | Job remained queued through API restart and completed after worker restart; one attempt |
| Mock smoke | Succeeded; decoded 5-second, 44.1 kHz stereo WAV was non-silent |
| Readiness after recovery | API reported `ready`; DB, schema, artifacts, dispatcher, mock worker, broker observation and provider were ready |

The browser run covered the capability UI at all four sizes, missing-project
alert semantics at all four sizes, generation/playback, and the desktop Phase 4
library/project/settings flow. That library flow now passes with its search
result visible. The D03 persisted-real-result browser case was skipped because
this isolated mock stack did not contain a persisted real-model result. Other
skips are desktop-only stateful checks repeated in responsive projects.

## Compose resolution

`docker compose config --services` passed for mock-only, YuE2-only and combined
diagnostic profiles. The exact service lists are in
[`compose-profiles.txt`](compose-profiles.txt). This verifies profile selection,
not a new YuE2 inference run. The mock-only image and real-service tests exercised
the independent mock queue; provider-route tests also passed. Current YuE2
capability claims remain bounded by the audited matrix in
[`docs/model-integration.md`](../../../../model-integration.md).

## Commands and attachments

The isolated Docker gate was run from the source checkout with:

```sh
MUSEFORGE_TEST_PROJECT_PREFIX=museforge-phase2-test-phase5- \
PHASE4_BROWSER=1 python3 scripts/verify-phase2.py
```

Attached outputs: [`integration.txt`](integration.txt), [`browser.txt`](browser.txt),
[`queued-restart.json`](queued-restart.json), [`restart.json`](restart.json),
[`readiness.json`](readiness.json), and [`mock-smoke.json`](mock-smoke.json).
The harness removed only its named containers, network and volumes after the
successful run. It left no test-prefixed containers or volumes behind.

## Capability boundary

The mock remains a deterministic demo provider: it accepts and preserves user
lyrics, returns scripted demo lyric text for its demo mode, and emits validated
non-silent WAV audio at the requested duration. It does not sing lyrics or
semantically follow music controls.

The pinned YuE2 provider accepts English user lyrics and has one prior durable
application result retrieved and played through the API; see the linked D03
application evidence. This proves route transport and technical audio handling.
It does not establish lyric adherence, vocal or instrumental behavior, language
fidelity, style-control fidelity, duration control, or cross-runtime seed
reproducibility. Audio conditioning, editing and continuation remain unsupported.
A fresh real YuE2 inference and the optional CPU-model inference test were not
part of this Phase 05 regression run. Release acceptance and Part 2 D04/D05
remain separate work.
