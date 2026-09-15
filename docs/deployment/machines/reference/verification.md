# YuE2 verification: reference deployment

The complete dated record is [evidence/2026-09-14-yue2](../../evidence/2026-09-14-yue2/README.md).

| Check | Result | Evidence |
| --- | --- | --- |
| Pinned image build and `pip check` | passed | `build.log`, `harness-build.log` |
| Host → WSL → container GPU visibility | passed | `gpu-preflight.json` and `runtime.json` |
| PyTorch CUDA 12.8 / BF16 / tensor operation | passed | `gpu-preflight.json` |
| Model/VAE immutable acquisition and file hashes | passed | `verified-models.json`, `acquire.log` |
| Bash syntax and Compose resolution | passed | `harness-tests.log`, build/run logs |
| Audio/process harness | 9 tests passed | `harness-tests.log` |
| Acoustic folk, seed 42 | passed; 99.00 s | batch `report.json` |
| Upbeat synth-pop, seed 43 | passed; 42.08 s | batch `report.json` |
| Piano ballad, seed 44 | passed; 82.04 s | batch `report.json` |
| Fresh-container folk repeat | passed; identical FLAC/PCM | restart `report.json`, `restart-comparison.json` |
| GPU memory recovery | passed after all 4 attempts | batch/restart reports |
| Real MuseForge queued job | pending | No application adapter/route yet |
| Browser playback and lyric adherence | pending | No listening tool; no app real path |

The generated audio is technically valid 48 kHz stereo FLAC, finite and nonempty,
with no planning/semantic token truncation. The supervisor recorded bounded GPU,
process-tree, and host-memory use throughout the run. Exact host-capacity figures
are retained only in the ignored local originals; these measurements are not
capacity or throughput guarantees.

The standalone image and report prove the model can execute on this target. They
do not prove that the MuseForge application can expose the model's capabilities,
persist its provenance, serve its artifacts, or maintain job lifecycle behavior.
