# YuE2 CPU smoke image

This is an isolated experiment for checking whether the newer upstream YuE2
runtime can execute a tiny request without CUDA. It does not replace the
CUDA-based production image or enable CPU YuE2 in MuseForge.

The image installs CPU PyTorch and the upstream YuE source at commit
the YuE main commit `0edaf2f4053ef4731334b8329834b107977f9637`, forces
`CUDA_VISIBLE_DEVICES` empty, and uses
`YuE2Pipeline(..., device="cpu", backend="torch-eager")`. The smoke request
skips symbolic planning and generates 32 codec tokens, so it is intentionally
truncated and is not a quality or full-song acceptance test.

Build and run from this directory:

```bash
docker compose -f compose.yaml build
docker compose -f compose.yaml run --rm acquire
docker compose -f compose.yaml run --rm smoke
```

The model snapshot is still approximately 7.3 GiB plus the VAE, so a CPU VM
needs substantial RAM and disk even for this tiny output. The smoke output is
written to the `outputs` volume as `cpu-smoke.wav`.
