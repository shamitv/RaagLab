# MuseForge Part 2 deployment plan

- Plan date: 2026-09-14
- Target class: reference Ubuntu/WSL2 deployment
- Topology: Ubuntu LTS inside WSL2, with Docker Engine running in the distribution
- Source workspace: repository root; the exact host path is local-only
- Current branch: `codex/part2-d04-d05-deployment`

## Scope and current outcome

This record covers the Part 2 model/image work and the integrated D03–D05 YuE2 route.
The standalone checkpoint, target mock gate, and real application gate are complete: one durable
YuE2 job passed through PostgreSQL, RabbitMQ, the dispatcher, and the real worker,
and its 48 kHz stereo result was retrieved and played through the API. The portable
application still defaults to mock mode; the real profile is explicit.

The eventual production path remains:

```text
Browser -> API -> PostgreSQL/outbox -> RabbitMQ -> real worker
        -> persisted model audio -> API playback/download -> browser
```

The standalone checkpoint exercises image/model setup, GPU access, process bounds,
audio validation, and repeatability. The separate integrated D03 evidence closes
the narrow application-queue gate; Phase 05 capability readiness is complete,
while target deployment, recovery, backup, restore, and handoff checks are recorded in D04/D05.

## Selected model and image

YuE2-3B was selected for this feasibility checkpoint because it generates songs
from a style prompt and supplied lyrics. The exact model revision is
`m-a-p/YuE2-3B@29b3558dd46954a0cd9021dc76d5c91864a0f1c7`; the decoder is
`m-a-p/YuE2-Vae@9a94e1d0ea9f8087e98f77fa88df4a4068104d2a`. Both model snapshots
use CC BY-NC 4.0 weights. The inference package is the official
`yue2-infer==0.1.5` wheel, pinned by URL and SHA-256.

The local image is `museforge-yue2:0.1.5`, based on the pinned Python 3.12
slim-bookworm image, PyTorch 2.10.0+cu128, and CUDA 12.8 wheels. Model files are
acquired separately into the persistent Docker volume
`museforge-yue2-weights`; the image contains no weights. Generated results
are retained in `museforge-yue2-validation-outputs`. See the [deployment manifest](machines/reference/deployment-manifest.md)
and [verification record](machines/reference/verification.md) for measured outcomes
and resource limits.

The reference host exposed a compatible NVIDIA GPU and passed the bounded gate.
Because it did not meet every upstream recommendation, the result remains a
feasibility checkpoint with one inference at a time and no claim about maximum
context or concurrent generation. Exact host capacity is local-only.

## Deployment phases

| Phase | State | Scope and exit gate |
| --- | --- | --- |
| D00 Inventory and plan | completed | Target, topology, model decision, gaps, and acceptance checks recorded |
| D01 Host preparation | completed | WSL/Docker/NVIDIA path and isolated deployment configuration are verified |
| D02 Mock deployment | completed on the reference host | Target browser playback, persistence, cancellation, and restart/recovery checks passed |
| D03 Real model | completed | Corrected integrated worker passed one durable real API job, verified provenance, 48 kHz retrieval/playback, and Phase 4-baseline regressions; [evidence](evidence/2026-09-14-d03-review-corrections/README.md) |
| D04 System validation | completed | Real readiness, queued job, provenance, audio retrieval/range checks, and queued cancellation passed |
| D05 Operations and handoff | completed | Runbook, manifest, backup/restore, isolated playback, update, rollback, and portability evidence passed |

The prior mock acceptance on the separate VM remains preserved in
`docs/implementation/evidence/02/2026-09-13-mock-end-to-end/`; it is not silently
reclassified as a reference-host deployment.

## Acceptance and recovery rules

Model acquisition must verify immutable revisions and remain outside Git and image
layers. The real worker must fail clearly when its adapter, weights, device, or
configuration is unavailable; it must never fall back to mock output. Inference
must initialize in the worker process, use one active request per GPU, maintain
bounded shutdown/cancellation behavior, validate audio before publication, and
persist model provenance with the result.

The standalone evidence is [here](evidence/2026-09-14-yue2/README.md), and the
integrated application evidence is [here](evidence/2026-09-14-d03-review-corrections/README.md).
The dated reference-host deployment passed the runbook gates. Live state is
recorded locally. Native Linux remains documented only, and the product
capability limitations remain explicit.
