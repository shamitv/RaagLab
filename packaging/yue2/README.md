# Standalone YuE2 test

This isolated image uses the official YuE2 inference wheel and default YuE2-Vae.
The base image, all Python dependencies, wheel hash, and both model revisions are
pinned. Model and decoder weights are CC BY-NC 4.0; this is a local test deployment.
Nothing is added to the MuseForge API or existing worker dependency environment.

## Build and acquire

Use the existing Ubuntu1 WSL Docker engine. If GPU passthrough is not configured,
run `setup-gpu.sh` as root there. It configures NVIDIA Container Toolkit 1.19.0 and
restarts Docker; stop unrelated workloads before running it.

From this directory in WSL:

```bash
docker build -t musicgen-yue2:0.1.5 .
docker volume create musicgen-yue2-test_weights
docker run --rm -v musicgen-yue2-test_weights:/weights musicgen-yue2:0.1.5
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
