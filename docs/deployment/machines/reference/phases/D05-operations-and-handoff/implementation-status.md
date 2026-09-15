# D05 implementation status

D05 completed on the reference host on 2026-09-15.

- Private setup generated credentials once and preserved them under the Linux
  deployment root.
- `drain.sh` stopped the dispatcher, waited for active jobs to reach zero, and
  stopped the worker with a bounded timeout.
- `backup.sh real` produced a PostgreSQL custom-format dump, artifact archive,
  non-secret manifest, and SHA-256 checksums at
  `$BACKUP_ROOT/20260915T031832Z`.
- `restore.sh` restored into an isolated restore project on a local test port after
  preserving the backup workspace identity. One restored active version retrieved
  playable audio with a matching hash; version IDs remained unique.
- `update.sh real` rebuilt the pinned worker and restarted the primary project
  without deleting volumes.
- `rollback.sh real` restored the same verified backup into a new
  an isolated rollback project on a separate local test port; playback and hash checks passed.
- Disposable restore and rollback containers/networks were removed; their volumes
  were preserved. The primary real project passed its final readiness check;
  current live state and local port ownership are recorded outside Git.

Native Linux remains documented only. The integrated runbook, manifest, and
portability matrix carry the remaining model and listening limitations.
