# Phase 06 normal-mode CPU gate — blocked prerequisite

Date: 2026-09-15. The required `bash scripts/test.sh release --real-cpu`
runtime gate was not started because the selected Linux host does not meet its
declared resource and model prerequisites.

## Host inspection

| Check | Observation | Required |
| --- | --- | --- |
| Host | `<verification-host>` | Authorized Linux Docker host |
| Docker Engine | 29.8.0 | Linux Docker engine |
| CPU configuration | Four worker threads configured | Four configured worker threads |
| Memory gate | Below the required threshold | At least 32 GiB before model startup |
| Verified weights volume | `museforge-yue2-weights` absent | Pinned read-only model and VAE volume |

The host is therefore unsuitable for normal-mode 3B CPU inference. The runner
was invoked from the disposable release checkout and stopped at its bounded
32 GiB memory preflight (exit code 1). Exact host inventory is retained only in
the ignored local originals.
It retained `failure.json`, `services.log`, `resource-samples.json`, and
`cleanup-down.log`; no model container was started, no weights were copied, and
no deployment volumes were deleted. The mock release evidence remains valid
and independent.

## Required follow-up

Run the gate from a clean checkout on a Linux Docker host with at least 32 GiB
available RAM and the existing verified `museforge-yue2-weights` volume:

```bash
bash scripts/test.sh release --real-cpu
```

The gate must pass normal planning, CPU/`torch-eager` provenance, nontruncated
validated audio, API retrieval checks, resource samples, and checksum
preservation across stop/start before Phase 06 can be marked complete.
