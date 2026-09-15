# D05 implementation status

D05 completed on Ubuntu1 on 2026-09-15.

- Private setup generated credentials once and preserved them under the Linux
  deployment root.
- `drain.sh` stopped the dispatcher, waited for active jobs to reach zero, and
  stopped the worker with a bounded timeout.
- `backup.sh real` produced a PostgreSQL custom-format dump, artifact archive,
  non-secret manifest, and SHA-256 checksums at
  `/home/shamit/.local/share/museforge-ubuntu1/backups/20260915T031832Z`.
- `restore.sh` restored into `museforge-ubuntu1-restore` on port 18000 after
  preserving the backup workspace identity. One restored active version retrieved
  playable audio with a matching hash; version IDs remained unique.
- `update.sh real` rebuilt the pinned worker and restarted the primary project
  without deleting volumes.
- `rollback.sh real` restored the same verified backup into a new
  `museforge-ubuntu1-rollback` project on port 19000; playback and hash checks passed.
- Disposable restore and rollback containers/networks were removed; their volumes
  were preserved. The primary real project was left healthy on port 8000.

Native Linux remains documented only. The integrated runbook, manifest, and
portability matrix carry the remaining model and listening limitations.
