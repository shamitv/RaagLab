# Phase 06 normal-mode CPU gate — blocked prerequisite

Date: 2026-09-15. The required `bash scripts/test.sh release --real-cpu`
runtime gate was not started because the selected Linux host does not meet its
declared resource and model prerequisites.

## Host inspection

| Check | Observation | Required |
| --- | --- | --- |
| Host | `yolo1@10.42.0.42` | Authorized Linux Docker host |
| Docker Engine | 29.8.0 | Linux Docker engine |
| CPUs | 4 | 4 configured worker threads |
| Total memory | 10 GiB | At least 32 GiB available host memory prerequisite |
| Available memory | About 7.3 GiB | At least 32 GiB before model startup |
| Verified weights volume | `musicgen-yue2-test_weights` absent | Pinned read-only model and VAE volume |

The host is therefore unsuitable for normal-mode 3B CPU inference. The runner
was invoked from the disposable release checkout and stopped at its bounded
preflight with `host has 7.2 GiB available; 32 GiB required` (exit code 1).
It retained `failure.json`, `services.log`, `resource-samples.json`, and
`cleanup-down.log`; no model container was started, no weights were copied, and
no deployment volumes were deleted. The mock release evidence remains valid
and independent.

## Required follow-up

Run the gate from a clean checkout on a Linux Docker host with at least 32 GiB
available RAM and the existing verified `musicgen-yue2-test_weights` volume:

```bash
bash scripts/test.sh release --real-cpu
```

The gate must pass normal planning, CPU/`torch-eager` provenance, nontruncated
validated audio, API retrieval checks, resource samples, and checksum
preservation across stop/start before Phase 06 can be marked complete.
