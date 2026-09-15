# Phase 06 release evidence

This directory contains the compact verification record for each published
Phase 06 run. The runner writes verbose, disposable command logs and browser
attachments to ignored `test-results/phase6-<run-id>/`; copy only the concise
report and links needed for review here.

Run from a clean configured checkout on a Linux Docker engine:

```bash
bash scripts/test.sh release
```

Add `--real-cpu` when the host has at least 32 GiB available memory and the
external verified `museforge-yue2-weights` volume:

```bash
bash scripts/test.sh release --real-cpu
```

The release record must identify the source revision, lock/image/runtime
versions, migration head, sanitized configuration, A01–A12 result, persistence
checks, browser coverage, and any skipped or blocked checks. Mock release
evidence does not claim real-model semantic quality. Part 2 D04/D05 deployment
evidence is published under `docs/deployment/evidence/`; the current CPU gate
prerequisite block is recorded in [20260915-cpu-gate-blocked](20260915-cpu-gate-blocked/README.md).
