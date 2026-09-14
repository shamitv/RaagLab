# Machine inventory: ubuntu1

## Observed 2026-09-14

- Windows host with WSL2 distribution `Ubuntu1`.
- Distribution: Ubuntu 24.04.5 LTS; kernel `6.6.87.2-microsoft-standard-WSL2`.
- Default WSL user: `shamit`; Docker access is available through the `docker`
  group. The Docker daemon runs inside WSL; context is `default`.
- CPU: 24 logical processors.
- WSL memory: 31.06 GiB total, about 30 GiB available during the test; swap 8 GiB.
- Root filesystem: 1007 GiB total, about 892 GiB available at inventory time.
- GPU: NVIDIA GeForce RTX 5080 Laptop GPU, 16,303 MiB total VRAM, driver 592.01.
- Docker: Engine 29.8.0, Linux containers; Compose v5.5.1.
- NVIDIA Container Toolkit: 1.19.0.
- No application ports were listening during inventory; no MuseForge test
  containers remained running after the standalone run.

## Topology and paths

The selected topology is Docker Engine running directly in WSL2, using the
Windows NVIDIA driver integration. A conventional Linux NVIDIA display/kernel
driver was not installed in WSL. The test source was the shared workspace at
`/mnt/c/work/musicgen`; persistent model and output data were Docker named
volumes, outside the repository and image layers:

- `musicgen-yue2-test_weights` — verified YuE2 and VAE snapshots.
- `musicgen-yue2-test_outputs` — generated audio, official artifacts, logs, and reports.

The exported review copy is `C:\work\musicgen\.local\yue2-results` and is ignored
by Git. No credentials or tokens were copied into this inventory.

## Evidence and assumptions

Host, WSL, container, and PyTorch GPU visibility were checked in sequence. The
standalone model authors recommend 24 GB VRAM, so this 16 GB device is treated as
a tested feasibility point with one request at a time. Network access was used
only during image dependency/model acquisition; inference containers ran with
`network_mode: none` and offline Hub settings.
