# YuE2 standalone runbook: ubuntu1

Run these commands from `/mnt/c/work/musicgen/packaging/yue2` inside the Ubuntu1
WSL distribution. They are the tested standalone commands; they do not start the
MuseForge API or alter its database.

## Build and acquire

```bash
docker build -t musicgen-yue2:0.1.5 .
docker compose config --quiet
docker compose run --rm test python preflight.py
docker compose run --rm acquire
```

`preflight.py` must report CUDA, BF16, capability 12.0, and a successful CUDA
matrix operation. `acquire` verifies both pinned model revisions and writes
`/weights/verified.json`. Keep the weights volume when rebuilding the image.

If the existing Docker Engine needs GPU configuration, run `setup-gpu.sh` as root
inside WSL. It installs only NVIDIA Container Toolkit 1.19.0, configures Docker,
and restarts that existing daemon; it does not install a Linux GPU driver. Verify
with `docker run --rm --gpus all nvidia/cuda:13.0.0-base-ubuntu24.04 nvidia-smi`.

## Test and restart

```bash
docker compose run --rm test python -m unittest -v test_harness
docker compose run --rm test
docker compose run --rm test python run.py --only acoustic-folk --label restart
```

The test service has no network, no published ports, read-only weights, a 28 GiB
container memory limit, and one GPU. `run.py` creates a timestamped report under
`/outputs`, supervises each inference in a separate process, retries only CUDA OOM
with AR offloading, and refuses the next request if GPU memory does not recover.

## Inspect and preserve results

```bash
docker volume inspect musicgen-yue2-test_outputs
docker run --rm --network none \
  -v musicgen-yue2-test_outputs:/source:ro \
  -v musicgen-yue2-test_weights:/weights:ro \
  -v /mnt/c/work/musicgen/.local:/export \
  -v /mnt/c/work/musicgen/.local/yue2-evidence/export.py:/export.py:ro \
  --entrypoint python musicgen-yue2:0.1.5 /export.py
```

Do not use `docker compose down -v` while evidence or weights are needed. Generated
audio is ignored by Git. The standalone test has no application URL; API/mock
start, stop, migration, and browser commands remain in the portable application
runbook and have not been reclassified as real-model commands.

## Failure handling

An OOM creates `failure.json` and triggers one offload retry. Other inference
errors, a timeout, failed audio validation, missing weights, or unrecovered GPU
memory leave the attempt evidence and make the supervisor exit nonzero. Do not
switch model, prompt, duration, precision, or provider silently. Inspect the
attempt `process.log` and `failure.json`, then resolve the stated requirement.
