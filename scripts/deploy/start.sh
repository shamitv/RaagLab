#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
mode="${1:-mock}"
create_only=false
[[ "${2:-}" == --create-only ]] && create_only=true
[[ $# -le 2 ]] || fail 'Usage: scripts/deploy/start.sh [mock|real] [--create-only]'
"$ROOT/scripts/deploy/preflight.sh" "$mode"
services=( $(mode_services "$mode") )
if $create_only; then
  compose_with_mode "$mode" create --build "${services[@]}"
  echo "created stopped $mode deployment $PROJECT_NAME"
  exit 0
fi
stop_other_worker "$mode"
deployment_env
port="${APP_PORT:-8000}"
owner="$(docker ps --filter "publish=$port" --format '{{.Names}}' | head -n 1)"
[[ -z "$owner" || "$owner" == "$PROJECT_NAME-api-1" ]] || fail "127.0.0.1:$port is already owned by container $owner. Set APP_PORT to another port."
compose_with_mode "$mode" up -d --build --wait --wait-timeout 240 "${services[@]}"
deployment_env
echo "started $mode deployment $PROJECT_NAME at http://127.0.0.1:${APP_PORT:-8000}"
