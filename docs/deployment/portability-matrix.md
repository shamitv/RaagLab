# Deployment portability matrix

| Capability | Reference WSL2 deployment | Native Linux |
| --- | --- | --- |
| Host GPU visibility | verified with a compatible NVIDIA GPU and driver | documented only |
| WSL distribution / kernel | verified on Ubuntu/WSL2; exact host details are local-only | not applicable |
| Docker Engine / Compose | verified; versions are retained in dated dependency evidence | documented only |
| NVIDIA Container Toolkit | verified | documented only |
| Container GPU passthrough | verified with `--gpus all` | documented only |
| PyTorch CUDA/BF16/tensor operation | verified in YuE2 image | documented only |
| YuE2 model load and inference | verified through MuseForge queue | documented only |
| MuseForge mock application | verified with an isolated D02 project | documented only |
| MuseForge real queued application path | verified with a persistent reference project | pending |
| Linux filesystem deployment path | configuration checked; deployment data is under WSL Linux home | documented only |

The WSL result uses the existing Linux Docker Engine and Windows-provided WSL GPU
integration. It does not claim a native-Linux deployment or a Docker Desktop
topology. Production model/cache and database/artifact I/O use Linux filesystem
locations; the source checkout location is selected per host and recorded locally.
