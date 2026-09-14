# Part 2 deployment status

- State: `in_progress`
- Last updated: 2026-09-14
- Target: `ubuntu1` (Ubuntu 24.04.5 LTS in WSL2; Docker Engine in WSL)
- Current focus: D03 application integration after the standalone YuE2 checkpoint

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

## Remaining work

- Implement and test a MuseForge music-provider adapter for YuE2.
- Add real-provider configuration, queue routing, readiness, provenance, and
  explicit no-fallback behavior to the application.
- Re-run D02 mock deployment on this target if this machine becomes the deployment
  host; the existing mock evidence belongs to the separate VM.
- Send a real job through the application queue, persist and retrieve its audio via
  the API, then perform D04 browser/recovery checks.
- Write the operations/backup/restore handoff after the integrated path passes.

## Blockers and limitations

The real-model exit gate is open because no application job has used this image.
The product's exact-lyrics, vocal, language, editing, and continuation capabilities
remain unverified; standalone lyric prompts do not prove sung-word accuracy.
Listening quality and lyric adherence are pending because no listening tool was
available during the run. Native Linux execution is documented only, not tested.

## Latest verification

See the [dated YuE2 evidence](evidence/2026-09-14-yue2/README.md), including runtime
inventory, image/build logs, model hashes, three prompt reports, restart comparison,
and the nine harness tests. The next action is D03-04: implement the adapter and
route one short job through the existing application worker contract.
