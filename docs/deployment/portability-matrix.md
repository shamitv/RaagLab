# Deployment portability matrix

| Capability | WSL2 / Ubuntu1 | Native Linux |
| --- | --- | --- |
| Host GPU visibility | verified on host: RTX 5080, driver 592.01 | documented only |
| WSL distribution / kernel | verified: Ubuntu 24.04.5, WSL2 kernel 6.6.87.2 | not applicable |
| Docker Engine / Compose | verified: Docker 29.8.0, Compose 5.5.1 | documented only |
| NVIDIA Container Toolkit | verified: 1.19.0 | documented only |
| Container GPU passthrough | verified with `--gpus all` | documented only |
| PyTorch CUDA/BF16/tensor operation | verified in YuE2 image | documented only |
| YuE2 model load and inference | verified for standalone batch | documented only |
| MuseForge mock application | verified on separate VM; not re-run on Ubuntu1 | documented only |
| MuseForge real queued application path | pending | pending |
| Linux filesystem deployment path | configuration checked; test source was under `/mnt/c` | documented only |

The WSL result uses the existing Linux Docker Engine and Windows-provided WSL GPU
integration. It does not claim a native-Linux deployment or a Docker Desktop
topology. Production model/cache and database/artifact I/O should use Linux
filesystem locations where practical rather than a Windows-mounted source path.
