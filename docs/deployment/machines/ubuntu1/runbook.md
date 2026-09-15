# MuseForge integrated deployment runbook: ubuntu1

Run these commands from `/mnt/c/work/musicgen` inside the Ubuntu1 WSL distribution.
The deployment uses Docker Engine inside WSL2, Compose project `museforge-ubuntu1`,
loopback port 8000, private settings under
`/home/shamit/.local/share/museforge-ubuntu1`, and separate database, broker, and
artifact volumes. The existing D03 review project is independent and preserved.

## First setup and preflight

```bash
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1 \
  bash scripts/deploy/setup.sh
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1 \
  bash scripts/deploy/preflight.sh mock
```

Setup generates credentials once and preserves them. Change the port in the
private `.env` when needed; preflight rejects a port already used by another
process. The YuE2 weights volume is the immutable, previously verified
`musicgen-yue2-test_weights` volume.

## Start, stop, status, and logs

```bash
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1 bash scripts/deploy/start.sh mock
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1 bash scripts/deploy/status.sh
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1 bash scripts/deploy/logs.sh
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1 bash scripts/deploy/stop.sh
```

`stop.sh` preserves all named volumes. `start.sh mock` runs the portable CPU
worker. `start.sh real` stops only the project mock worker, starts the API,
dispatcher, and one GPU YuE2 worker, and leaves the D03 project untouched.

## Real provider and verification

```bash
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1 bash scripts/deploy/start.sh real
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1 bash scripts/deploy/verify.sh real
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1 bash scripts/deploy/recovery.sh real
```

The real verifier submits through the API and queue, checks model and revision
provenance, persists and retrieves audio, validates WAV metadata and byte ranges,
and records evidence under the private deployment root. Recovery covers a real
queued cancellation. Repeatable broker, dispatcher, worker-loss, and full
restart checks run in the isolated mock verifier:

```bash
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1 bash scripts/deploy/verify.sh mock
```

## Drain, backup, restore, and update

```bash
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1 bash scripts/deploy/drain.sh real
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1 bash scripts/deploy/backup.sh real
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1 bash scripts/deploy/update.sh real
MUSEFORGE_PROJECT_NAME=museforge-ubuntu1-restore \
MUSEFORGE_DEPLOY_ROOT=/home/shamit/.local/share/museforge-ubuntu1-restore \
  bash scripts/deploy/restore.sh /home/shamit/.local/share/museforge-ubuntu1/backups/<timestamp>
```

Backup stops the dispatcher and workers after a bounded drain, dumps PostgreSQL
with `pg_dump -Fc`, archives the project artifact volume, writes a non-secret
manifest, and records SHA-256 checksums. Restore refuses the production project
name and requires a new database, broker, and artifact target. `rollback.sh`
refuses an unverified or incomplete backup; use restore as the tested rollback
path when a schema downgrade is not compatible.

Model initialization failures, missing weights, missing GPU access, OOM, timeout,
and invalid audio leave an actionable failure and never fall back to mock output.

## WSL recovery

After a WSL shutdown or Windows reboot, start the selected WSL distribution and
Docker Engine, then rerun `scripts/deploy/status.sh` and `start.sh real` if the
project is stopped. Do not use a host-wide `docker stop`, `wsl --shutdown`, or
volume deletion as part of ordinary application updates; the D03 review project
and its volumes are separate and must remain undisturbed.

## Portability and limitations

The WSL2 path is verified on Ubuntu1. Native Linux is configuration-checked and
documented only. The real model gate proves one English user-lyrics technical
route. It does not prove sung lyric adherence, language breadth, exact duration,
musical control fidelity, instrumental quality, or subjective listening quality.
