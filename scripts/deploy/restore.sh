#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
backup="${1:-}"
[[ -d "$backup" ]] || fail 'usage: restore.sh BACKUP_DIR'
[[ -f "$backup/SHA256SUMS" && -f "$backup/manifest.json" && -f "$backup/database.dump" && -f "$backup/artifacts.tar" ]] || fail 'backup is incomplete'
(cd "$backup" && sha256sum -c SHA256SUMS)
[[ "$PROJECT_NAME" != "$DEFAULT_PROJECT_NAME" ]] || fail 'restore requires a new MUSEFORGE_PROJECT_NAME'
require_env; require_engine; ensure_dirs; write_mode_env mock
workspace_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["workspace_id"])' "$backup/manifest.json")"
sed -i "s/^WORKSPACE_ID=.*/WORKSPACE_ID=$workspace_id/" "$DEPLOY_ENV_FILE"
write_mode_env mock
compose_with_mode mock up -d --wait --wait-timeout 180 db broker
deployment_env
compose_with_mode mock exec -T db dropdb -U "$POSTGRES_USER" --if-exists "$POSTGRES_DB"
compose_with_mode mock exec -T db createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
cat "$backup/database.dump" | compose_with_mode mock exec -T db pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner
artifact_volume="${PROJECT_NAME}_artifacts"
docker run --rm --network none -v "$artifact_volume:/target" -v "$(cd "$backup" && pwd):/backup:ro" alpine:3.22 sh -c 'rm -rf /target/* /target/.[!.]* 2>/dev/null || true; tar -xf /backup/artifacts.tar -C /target'
compose_with_mode mock up -d --wait --wait-timeout 240 api dispatcher worker-mock
echo "restore_complete project=$PROJECT_NAME; verify with scripts/deploy/verify.sh mock"
