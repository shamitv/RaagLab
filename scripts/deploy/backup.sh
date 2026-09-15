#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
mode="${1:-real}"
require_env; require_engine; write_mode_env "$mode"; deployment_env
ensure_dirs
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
destination="${2:-$BACKUP_ROOT/$stamp}"
mkdir -p "$destination"; chmod 700 "$destination"
"$ROOT/scripts/deploy/drain.sh" "$mode"
compose_with_mode "$mode" exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$destination/database.dump"
artifact_volume="${PROJECT_NAME}_artifacts"
docker run --rm --network none -v "$artifact_volume:/source:ro" -v "$destination:/backup" alpine:3.22 tar -cf /backup/artifacts.tar -C /source .
revision="$(git -C "$ROOT" rev-parse HEAD)"
image_ids="$(compose_with_mode "$mode" images --format json 2>/dev/null | python3 -c 'import json,sys; print(json.dumps([json.loads(line) for line in sys.stdin if line.strip()]))' || printf '[]')"
cat > "$destination/manifest.json" <<EOF
{
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "project": "$PROJECT_NAME",
  "mode": "$mode",
  "source_revision": "$revision",
  "database_dump": "database.dump",
  "artifact_archive": "artifacts.tar",
  "workspace_id": "$WORKSPACE_ID",
  "model_id": "${MODEL_ID:-}",
  "model_revision": "${MODEL_REVISION:-}",
  "decoder_revision": "${DECODER_REVISION:-}",
  "compose_images": $([ -n "$image_ids" ] && printf '%s' "$image_ids" || printf '[]')
}
EOF
(cd "$destination" && sha256sum database.dump artifacts.tar manifest.json > SHA256SUMS)
echo "backup_complete=$destination"
