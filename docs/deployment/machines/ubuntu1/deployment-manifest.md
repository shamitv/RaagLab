# Deployment manifest: ubuntu1

- Validation date: 2026-09-15
- Source branch: `codex/part2-d04-d05-deployment`
- Compose project: `museforge-ubuntu1`
- Compose files: `compose.yaml`, `compose.yue2.yaml`, `compose.yue2.gpu.yaml`, `deploy/compose/compose.ubuntu1*.yaml`
- Application URL: `http://127.0.0.1:8000`
- Deployment root: `/home/shamit/.local/share/museforge-ubuntu1` (private)
- Database/broker/artifact volumes: `museforge-ubuntu1_database`, `museforge-ubuntu1_broker`, `museforge-ubuntu1_artifacts`
- Weights volume: `musicgen-yue2-test_weights` (read-only during inference)

## Model and runtime

- Model: `m-a-p/YuE2-3B@29b3558dd46954a0cd9021dc76d5c91864a0f1c7`
- Decoder: `m-a-p/YuE2-Vae@9a94e1d0ea9f8087e98f77fa88df4a4068104d2a`
- License: CC BY-NC 4.0 weights
- Inference package: `yue2-infer` pinned by `packaging/yue2/requirements.lock`; runtime reported 0.1.6
- Python 3.12.14; PyTorch 2.10.0+cu128; CUDA 12.8; BF16
- GPU: RTX 5080 Laptop, 16,303 MiB VRAM; one active inference
- Runtime budget: 16 GiB; FP32 VAE; no quantization; full symbolic planning
- Generation deadline: 900 seconds; 5-second graceful process termination, followed by kill/reap

## Provider state

The active MuseForge application provider is `yue2` in the persistent deployment;
the mock profile remains available as a diagnostic path. Exact lyric adherence,
language breadth, musical control, instrumental fidelity, and subjective
listening quality remain unverified.

## Results

The integrated verifier completed one durable queued job with one attempt, CUDA
provenance, 48 kHz stereo WAV retrieval, HEAD and byte-range checks, and a
77.2387-second measured result for an 8-second request. D02 passed 49 integration
checks and 34 browser checks with 22 intentional skips. See the [dated record](../../evidence/2026-09-15-d04-d05/README.md).
