#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
mode="${1:-real}"
backup="${2:-}"
[[ "$mode" == mock || "$mode" == real ]] || fail 'usage: rollback.sh mock|real BACKUP_DIR'
[[ -n "$backup" && -d "$backup" ]] || fail 'rollback requires a verified backup directory'
[[ -f "$backup/manifest.json" && -f "$backup/database.dump" && -f "$backup/artifacts.tar" ]] || fail 'backup is incomplete'
[[ "$PROJECT_NAME" != "$DEFAULT_PROJECT_NAME" ]] || fail 'rollback requires a new MUSEFORGE_PROJECT_NAME to preserve the active deployment'
"$ROOT/scripts/deploy/restore.sh" "$backup"
echo "rollback_restore_complete project=$PROJECT_NAME backup=$backup"
