# D03 real application and review-correction evidence

Date: 2026-09-14. Runtime: reference host, Docker Engine 29.8.0, compatible NVIDIA GPU
GPU, pinned Python 3.12/YuE2 0.1.5/CUDA 12.8 inference runtime. Integration branch:
`integration/d03-review-corrections`, based on Phase 4 merge `c546152`.

## Real application gate

The final worker build completed the public API → PostgreSQL/outbox → RabbitMQ
`museforge.yue2.v1` → real worker → persisted version/artifact → API path.

| Measurement | Result |
| --- | --- |
| Job | `0287f11a-e1af-4934-92ed-4f462148ed7f` |
| Project | `4af327ba-cbed-4be0-bd51-e68d6c0d2fdb` |
| Version | `2af1a847-5742-4056-b4d1-62730e5fd284` |
| Artifact | `7cd11c24-7252-4715-9f1c-a1a27956a49d` |
| Durable result | Succeeded; one attempt, one persisted version, one confirmed outbox entry for this job |
| Provider/model | `yue2` / `yue2-infer-0.1.5` / `m-a-p/YuE2-3B` |
| Model revision | `29b3558dd46954a0cd9021dc76d5c91864a0f1c7` |
| Decoder revision | `9a94e1d0ea9f8087e98f77fa88df4a4068104d2a` |
| Requested/measured duration | 8 seconds / 77.23866666666666 seconds |
| Published audio | 48,000 Hz; stereo; 16-bit PCM WAV; 3,707,456 frames; 14,829,868 bytes |
| WAV SHA-256 | `6743f76c4f20acb2d4847d9a8b96b78e33638f359d43d3856bdebe4713022288` |
| Adapter elapsed time | 48.73211648200231 seconds |
| Torch peak allocated/reserved | 8,441,164,288 / 8,690,597,888 bytes |
| Retrieval | Full GET, HEAD, and byte range 0–43 passed; retrieved SHA matched persisted metadata |
| Browser | Desktop Chromium playback advanced; seeking to 3 seconds passed |

The real Compose profile did not start a mock worker. Model weights were mounted
read-only from `museforge-yue2-weights`; only the worker mounted application
artifacts read-write. A separate earlier application probe also succeeded before
the final guardian refinement; the table records the final-build probe.

## Review corrections and checks

- The complete hash-locked application runtime was generated with pinned
  `uv==0.12.13`, Python 3.12/Linux constraints, and the inference lock. Actual
  installation of both locks and `pip check` passed. API and dispatcher image
  inspection found no `torch`, `transformers`, or `yue2` module.
- All four combinations of configured mock/real publisher and mock/real
  destination queue passed actual RabbitMQ publication. Wrong-route and
  wrong-model workers left a durable job queued with zero attempts; a matching
  synthetic provider subsequently completed that job using its exact persisted
  lyrics checkpoint. Synthetic audio is supporting test evidence only.
- Readiness matched provider, route, model, revisions, capability revision, and
  workspace. Recorded API transitions were offline → initializing → ready with
  YuE2 metadata. Custom deployment credentials/workspace and GPU/mount settings
  passed Compose resolution checks.
- Missing weights, missing model files, conflicting identity, and missing GPU
  each exited startup with code 78. Missing device produced typed
  `initialization_failure`. With the real worker stopped, a request remained
  queued with zero attempts and no result, then cancelled successfully.
- During actual YuE2 GPU planning, the owner of the guardian was killed. The
  inference process was reaped, replacement remained excluded until cleanup,
  and whole-device memory returned from 1,274,122,240 to its 314,572,800-byte
  baseline. The child recorded 757,071,872 allocated/reserved CUDA bytes before
  the kill. This is a disposable model-process check, not a second durable job.
- Linux tests additionally exercised an inference descendant that creates a new
  session and ignores SIGTERM. Cleanup killed and reaped it before releasing the
  lock. Ordinary cancellation, deadline, and shutdown checks passed.

## Reproduction and evidence location

Local Python tests passed 131 checks, including actual FLAC decoding and 48 kHz
PCM conversion. The pinned frontend suite passed three checks. The combined
mock run passed 48 integration and 30 browser checks (22 intentional skips), but
its first restart sweep exposed incomplete test fixtures: root-owned synthetic
audio needed API-readable permissions, and a Phase 4 GC live-attempt fixture
needed the outbox row required by API job serialization. Both corrections are
test-only; production storage, GC, and schema behavior are unchanged. The full
combined acceptance run then passed with these complete fixtures:

- Container Python: 129 passed, two expected skips; both skipped checks passed
  locally. Frontend: three passed. Integration: 48 passed.
- Mock browser: 30 passed, 22 intentional skips (18 existing viewport-specific
  skips and four gated real-result tests). Real-result browser: one passed.
- Queued/idempotent API restart, artifact retrieval sweep, ambiguous confirmed
  publication, dispatcher restart, broker recovery, killed-worker lease/fencing
  recovery, volume-preserving full restart, and the existing demo smoke passed.
- Final combined evidence: `test-results/museforge-phase4-test/`;
  command log: `test-results/d03-mock-regression-final.log`. D03 is completed.

Run from `<repository-root>` on the reference host. Build/start an isolated stack with:

```sh
docker compose --project-name museforge-reference-validation --profile yue2 \
  -f compose.yaml -f compose.yue2.yaml build api dispatcher worker-yue2
APP_PORT=0 docker compose --project-name museforge-reference-validation --profile yue2 \
  -f compose.yaml -f compose.yue2.yaml up -d api dispatcher worker-yue2
```

After configured readiness is ready, run `scripts/verify-d03.py` inside the
dispatcher container, mounting the script read-only and an evidence directory at
`/tmp/d03-evidence`. It submits a new real request and verifies durable counts,
provenance, WAV decoding, hash, and retrieval. Run the gated Playwright
`d03-real.spec.ts` with `API_BASE_URL` and the resulting `D03_PROJECT_ID`.

`scripts/verify-d03-config.py` resolves disposable custom deployment settings.
`scripts/verify-d03-startup-failures.py` checks the isolated stack's startup
failures. Stop only its real worker before running
`scripts/verify-d03-unavailable.py`. `scripts/verify-d03.py --readiness-only`
records the next restart transition. Run `scripts/verify-yue2-supervision.py
--real-model` in the integrated GPU image while other inference is idle.

Detailed JSON, logs, the retrieved WAV, and browser screenshot/trace remain in
ignored `test-results/d03-real-acceptance/`. Build and unit logs use
`test-results/d03-*.log`. Weights and generated audio are not committed.

## Limits

This proves one narrow English user-lyrics application route and technical audio
validity. It does not prove sung lyric adherence, broader language support, true
instrumental output, musical-control fidelity, or subjective quality. Duration is
model-determined. The 16 GB GPU remains below the upstream 24 GB recommendation.
