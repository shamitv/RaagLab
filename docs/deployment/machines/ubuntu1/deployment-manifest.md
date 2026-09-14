# Deployment manifest: ubuntu1

- Validation date: 2026-09-14
- Source branch: `model_deploy`
- Source commits: `784d262`, `c5400a2`, `e552121`
- Standalone image: `musicgen-yue2:0.1.5`
- Image ID: `sha256:625a4cc64bc869b1d6b0a642d2803b5ab5939bfcc513b6d95468bb1968b000ac`
- Image size: 12,028,725,411 bytes
- Compose file: `packaging/yue2/compose.yaml`
- Application URL: none; this is a batch test with no published port
- Weights volume: `musicgen-yue2-test_weights` (read-only during inference)
- Results volume: `musicgen-yue2-test_outputs`
- Review export: `C:\work\musicgen\.local\yue2-results`

## Model and runtime

- Model: `m-a-p/YuE2-3B@29b3558dd46954a0cd9021dc76d5c91864a0f1c7`
- Decoder: `m-a-p/YuE2-Vae@9a94e1d0ea9f8087e98f77fa88df4a4068104d2a`
- License: CC BY-NC 4.0 weights
- Inference package: `yue2-infer==0.1.5`; wheel SHA-256
  `8801e2c0d969db02df78d2994150b4ccd86077d87c24fdb8509b1f6f31462641`
- Python 3.12.14; PyTorch 2.10.0+cu128; CUDA 12.8; BF16
- GPU: RTX 5080 Laptop, 16,303 MiB VRAM; one active inference
- Runtime budget: 16 GiB; FP32 VAE; no quantization; full symbolic planning
- Generation deadline: 900 seconds; 5-second graceful process termination,
  followed by kill/reap; 15-second GPU recovery check

## Provider state

The active MuseForge application provider remains `mock`. The YuE2 image is a
standalone deployment artifact and is not configured as a MuseForge queue worker.
The real-provider adapter, application routing, API provenance, browser playback,
and real queued smoke are pending. The mock profile remains the diagnostic path.

## Results

Three prompts (seeds 42, 43, and 44) passed technical validation, producing 99.00,
42.08, and 82.04 seconds of 48 kHz stereo FLAC. A fresh-container repeat of seed
42 passed with identical FLAC and PCM hashes. Full measurements and limitations
are in [verification.md](verification.md) and the [dated evidence](../../evidence/2026-09-14-yue2/README.md).
