# Standalone YuE2 test

This isolated image uses official YuE2 0.1.6 source and default YuE2-Vae.
The base image, all Python/build dependencies, source hash, and both model revisions are
pinned. Model and decoder weights are CC BY-NC 4.0; this is a local test deployment.
Nothing is added to the MuseForge API or existing worker dependency environment.

## Build and acquire

Use the existing Ubuntu1 WSL Docker engine. If GPU passthrough is not configured,
run `setup-gpu.sh` as root there. It configures NVIDIA Container Toolkit 1.19.0 and
restarts Docker; stop unrelated workloads before running it.

From this directory in WSL:

```bash
docker build -t musicgen-yue2:0.1.6 .
docker volume create musicgen-yue2-test_weights
docker run --rm -v musicgen-yue2-test_weights:/weights musicgen-yue2:0.1.6
```

Acquisition uses `hf download` with immutable revisions, downloads only runtime
files and notices, then verifies SHA-256 for LFS files and Git blob hashes for
other files against the pinned Hub metadata. `/weights/verified.json` records
every acquired file's SHA-256. Weights remain outside Git and image layers.
Allow at least 12 GiB free for acquisition and additional space for the CUDA
image/build cache. Downloads resume using the persistent volume's Hub metadata.

To regenerate the dependency lock in the pinned Linux Python 3.12 base image:

```bash
python -m pip install uv==0.12.13
uv pip compile --python-version 3.12 --torch-backend cu128 --generate-hashes \
  requirements.in -o requirements.lock
```

The build installs that lock using pip's `--require-hashes` and the CUDA 12.8
wheel index, then runs `pip check`. No access token is required for these public
repositories. No registry publishing or hosted inference is involved.

## Run the isolated test

```bash
docker compose build acquire
# Before model acquisition: verify CUDA/BF16/tensor computation.
docker compose run --rm test python preflight.py
docker compose run --rm acquire
docker compose run --rm test python -m unittest -v test_harness
docker compose run --rm test
# A fresh container and process repeat the first prompt using cached weights.
docker compose run --rm test python run.py --only acoustic-folk --label restart
```

`test` has no network or published ports. Weights mount read-only, temporary files
use tmpfs, and all reports/audio persist in `musicgen-yue2-test_outputs`. Each run
gets a unique timestamp directory. Inspect retained results with a temporary
container mounting that volume; export them with `docker cp` for local playback.
Do not use `docker compose down -v` if you want to retain weights and results.

The GPU must expose BF16. The host used for this test has 16 GB VRAM and about
31 GiB WSL RAM; upstream recommends 24 GB VRAM and 24 GB available host RAM.
This is therefore a feasibility test, not a claim of upstream hardware support.
The inference package receives a 16 GiB budget (it reserves 2 GiB internally),
BF16 AR/NAR, FP32 VAE, no quantization, full symbolic planning, and its default
sampling limits. Only CUDA OOM triggers one retry with `offload_ar=True`.
There is no automatic switch of model, device, precision, prompt, or token budget.

Each attempt runs in a new process. The supervisor samples whole-device GPU use
and process-tree RSS every 200 ms, enforces a 900-second deadline, allows 5 seconds
for SIGTERM, then SIGKILL/reaps. It checks device-memory recovery for up to 15
seconds, allowing 256 MiB noise for WSL/display use, and stops if memory remains
elevated. Measured NVML peaks include other GPU use; PyTorch allocation peaks are
also recorded per attempt. Each process loads the model afresh; this is not a
persistent-worker warm-throughput benchmark.

The fixtures contain original English lyrics and three styles. YuE2 determines
duration; reaching either token limit is recorded as truncation and fails full
completion. Technical acceptance requires 48 kHz stereo, more than 5 seconds,
finite decoded and pre-encoding samples, RMS above 0.0001, and less than 1% of
samples at absolute amplitude 0.999 or above. These are screening thresholds,
not perceptual-quality guarantees. FLAC and decoded-PCM hashes support the restart
comparison. Listening and lyric adherence stay pending until actually assessed.

`report.json` contains subprocess outcomes and resource measurements. Each
attempt folder contains logs, exact inputs, official generated artifacts,
`validation.json` or `failure.json`. The supervisor exits nonzero if any selected
song's final attempt fails; failed and baseline attempts remain available.
