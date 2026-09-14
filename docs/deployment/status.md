# Part 2 deployment status

- State: `in_progress`
- Last updated: 2026-09-14
- Target: `ubuntu1` (Ubuntu 24.04.5 LTS in WSL2; Docker Engine in WSL)
- Current focus: D02 target mock deployment, then D04 real workflow and recovery validation

## Completed

- D00 target inventory, topology, model decision, phase plan, and acceptance rules.
- NVIDIA Container Toolkit 1.19.0 configured for the existing WSL Docker Engine.
- Container-level NVIDIA visibility, PyTorch CUDA 12.8, BF16 support, capability
  12.0, and a CUDA tensor operation verified.
- Reproducible `musicgen-yue2:0.1.5` image built with hash-locked dependencies.
- YuE2-3B and YuE2-Vae snapshots acquired into a persistent volume and verified
  against immutable Hub revisions and file hashes.
- Three original prompt cases generated successfully; all audio checks passed.
- A fresh offline container repeated the first prompt with identical FLAC and PCM
  hashes. Every attempt released GPU memory; no OOM or timeout occurred.
- D03 integrated the YuE2 adapter, isolated worker image/queue, startup readiness,
  provenance, and no-fallback behavior. One durable application job produced a
  verified 48 kHz stereo result that was retrieved and played through the API.
  See the [D03 integration evidence](evidence/2026-09-14-d03-review-corrections/README.md).

## Remaining work

- Re-run D02 mock deployment on this target if this machine becomes the deployment
  host; the existing mock evidence belongs to the separate VM.
- Perform D04 browser, real workflow, cancellation, restart/recovery, and resource
  checks on this target after D02 is complete.
- Write the operations/backup/restore handoff after the integrated path passes.

## Blockers and limitations

The narrow real-model D03 gate passed. The product's exact-lyrics, vocal,
language, style-control, and requested-duration behavior remain unverified;
successful audio transport does not establish those capabilities.
Listening quality and lyric adherence are pending because no listening tool was
available during the run. Native Linux execution is documented only, not tested.

## Latest verification

See the [standalone YuE2 evidence](evidence/2026-09-14-yue2/README.md) and
[integrated D03 evidence](evidence/2026-09-14-d03-review-corrections/README.md).
The next action is D02 target deployment; D04 depends on both that target stack
and the completed D03 application route.
