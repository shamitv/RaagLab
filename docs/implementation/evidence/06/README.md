# Phase 06 release evidence

This directory contains the compact verification record for each published
Phase 06 run. The runner writes verbose, disposable command logs and browser
attachments to ignored `test-results/phase6-<run-id>/`; copy only the concise
report and links needed for review here.

Run from a clean configured checkout on a Linux Docker engine:

```bash
bash scripts/test.sh release
```

The release record must identify the source revision, lock/image/runtime
versions, migration head, sanitized configuration, A01–A12 result, persistence
checks, browser coverage, and any skipped or blocked checks. Mock release
evidence does not claim real-model semantic quality or Part 2 deployment.
