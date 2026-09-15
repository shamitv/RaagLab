#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
mode="${1:-mock}"
"$ROOT/scripts/deploy/preflight.sh" "$mode"
stop_other_worker "$mode"
services=( $(mode_services "$mode") )
compose_with_mode "$mode" up -d --build --wait --wait-timeout 240 "${services[@]}"
deployment_env
echo "started $mode deployment $PROJECT_NAME at http://127.0.0.1:${APP_PORT:-8000}"
