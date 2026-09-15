# MuseForge managed deployment runbook

Run all commands from the repository root on a Linux Docker engine. The managed
scripts default to project `museforge-managed` and private state under
`${XDG_DATA_HOME:-$HOME/.local/share}/museforge-managed`. Set the existing
`MUSEFORGE_DEPLOY_ROOT` and `MUSEFORGE_PROJECT_NAME` variables to operate a
different or pre-existing deployment. Keep exact host values in the ignored
local machine document created from
[`local-machine.template.md`](../../local-machine.template.md).

## First setup and preflight

```bash
bash scripts/deploy/setup.sh
bash scripts/deploy/preflight.sh mock
```

Setup generates credentials once and preserves them. Change the port in the
private `.env` when needed; preflight rejects a port already used by another
process. Real mode uses the external volume named by
`MUSEFORGE_YUE2_WEIGHTS_VOLUME`, defaulting to `museforge-yue2-weights`.

## Start, stop, status, and logs

```bash
bash scripts/deploy/start.sh mock
bash scripts/deploy/status.sh
bash scripts/deploy/logs.sh
bash scripts/deploy/stop.sh
```

`stop.sh` preserves named volumes. `start.sh mock` runs the portable CPU mock
worker. `start.sh real` stops only the same project's mock worker and starts the
API, dispatcher, and one YuE2 worker. Device mode supports
`YUE2_DEVICE=cpu|cuda|auto`; strict CUDA requires the NVIDIA runtime, while auto
adds the GPU override only when Docker advertises that runtime.

## Real provider and verification

```bash
bash scripts/deploy/start.sh real
bash scripts/deploy/verify.sh real
bash scripts/deploy/recovery.sh real
```

For explicit CPU operation, prefix the same commands with `YUE2_DEVICE=cpu`.
The complete isolated CPU release gate additionally checks normal-mode
generation, resource bounds, persistence, and cleanup:

```bash
bash scripts/test.sh release --real-cpu
```

It requires the configured verified weights volume and at least 32 GiB
available host memory. Repeatable broker, dispatcher, worker-loss, and full
restart checks run through `bash scripts/deploy/verify.sh mock`.

## Drain, backup, restore, and update

```bash
bash scripts/deploy/drain.sh real
bash scripts/deploy/backup.sh real
bash scripts/deploy/update.sh real

BACKUP_TO_RESTORE="${MUSEFORGE_BACKUP_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/museforge-managed/backups}/<timestamp>"
MUSEFORGE_PROJECT_NAME=museforge-managed-restore \
MUSEFORGE_DEPLOY_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/museforge-managed-restore" \
  bash scripts/deploy/restore.sh "$BACKUP_TO_RESTORE"
```

Backup drains work, dumps PostgreSQL, archives artifacts, writes a non-secret
manifest, and records checksums. Restore and rollback refuse the default active
project and require a complete verified backup.

## Recovery and limitations

After a host restart, confirm Docker is running, inspect
`scripts/deploy/status.sh`, and restart the selected mode if needed. Do not use
host-wide Docker shutdown or volume deletion during ordinary updates.

The WSL2 deployment path was verified; native Linux remains
configuration-checked only. The real-model gate proves a narrow English
user-lyrics technical route, not lyric adherence, language breadth, exact
duration, musical-control fidelity, instrumental quality, or subjective
listening quality.
