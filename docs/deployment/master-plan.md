# MuseForge Part 2 deployment plan

- Plan date: 2026-09-14
- Target alias: `ubuntu1`
- Topology: Ubuntu 24.04.5 LTS inside WSL2, with Docker Engine running in the distribution
- Source workspace: `C:\work\musicgen` (deployment test invoked through `/mnt/c/work/musicgen`)
- Current branch: `model_deploy`

## Scope and current outcome

This record covers the concrete Part 2 model and image work that followed the
portable mock application. The standalone real-model checkpoint is complete for
the selected test cases. The application remains in mock mode: YuE2 has not yet
been adapted to the MuseForge provider contract or routed through PostgreSQL,
RabbitMQ, the dispatcher, and the application worker.

The eventual production path remains:

```text
Browser -> API -> PostgreSQL/outbox -> RabbitMQ -> real worker
        -> persisted model audio -> API playback/download -> browser
```

The standalone checkpoint deliberately exercises only the worker-side model
image, persistent model acquisition, GPU access, process bounds, audio validation,
and restart behavior. It does not satisfy the D03 application-queue exit gate.

## Selected model and image

YuE2-3B was selected for this feasibility checkpoint because it generates songs
from a style prompt and supplied lyrics. The exact model revision is
`m-a-p/YuE2-3B@29b3558dd46954a0cd9021dc76d5c91864a0f1c7`; the decoder is
`m-a-p/YuE2-Vae@9a94e1d0ea9f8087e98f77fa88df4a4068104d2a`. Both model snapshots
use CC BY-NC 4.0 weights. The inference package is the official
`yue2-infer==0.1.5` wheel, pinned by URL and SHA-256.

The local image is `musicgen-yue2:0.1.5`, based on the pinned Python 3.12
slim-bookworm image, PyTorch 2.10.0+cu128, and CUDA 12.8 wheels. Model files are
acquired separately into the persistent Docker volume
`musicgen-yue2-test_weights`; the image contains no weights. Generated results
are retained in `musicgen-yue2-test_outputs`. See the [machine manifest](machines/ubuntu1/deployment-manifest.md)
and [verification record](machines/ubuntu1/verification.md) for measured IDs and
resource limits.

The observed GPU is an NVIDIA RTX 5080 Laptop GPU with 16,303 MiB VRAM. Upstream
documents a 24 GB recommendation; this plan therefore treats the 16 GB result as
a bounded feasibility checkpoint, with one inference at a time, a 16 GiB runtime
budget, and no claim about maximum context or concurrent generation.

## Deployment phases

| Phase | State | Scope and exit gate |
| --- | --- | --- |
| D00 Inventory and plan | completed | Target, topology, model decision, gaps, and acceptance checks recorded |
| D01 Host preparation | in_progress | WSL/Docker/NVIDIA path is verified; application deployment directories and startup configuration remain |
| D02 Mock deployment | not_started on `ubuntu1` | Re-run the existing DB/broker/API/mock worker path on this target and prove browser playback/restart |
| D03 Real model | completed | Corrected integrated worker passed one durable real API job, verified provenance, 48 kHz retrieval/playback, and Phase 4-baseline regressions; [evidence](evidence/2026-09-14-d03-review-corrections/README.md) |
| D04 System validation | not_started | Validate real capabilities, API playback, iterations, cancellation, restart, and resource limits |
| D05 Operations and handoff | not_started | Runbook, manifest, backup/restore, update/rollback, and portability handoff |

The prior mock acceptance on the separate VM remains preserved in
`docs/implementation/evidence/02/2026-09-13-mock-end-to-end/`; it is not silently
reclassified as an `ubuntu1` deployment.

## Acceptance and recovery rules

Model acquisition must verify immutable revisions and remain outside Git and image
layers. The real worker must fail clearly when its adapter, weights, device, or
configuration is unavailable; it must never fall back to mock output. Inference
must initialize in the worker process, use one active request per GPU, maintain
bounded shutdown/cancellation behavior, validate audio before publication, and
persist model provenance with the result.

The standalone evidence is [here](evidence/2026-09-14-yue2/README.md). The next
implementation step is to add the YuE2 provider adapter and a dedicated real queue
while retaining the working mock profile for diagnostics.
