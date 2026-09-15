#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
mode="${1:-real}"
[[ "$mode" == mock || "$mode" == real ]] || fail 'usage: update.sh mock|real'
"$ROOT/scripts/deploy/preflight.sh" "$mode"
revision="$(git -C "$ROOT" rev-parse HEAD)"
services=( $(mode_services "$mode") )
compose_with_mode "$mode" build "${services[@]}"
compose_with_mode "$mode" up -d --wait --wait-timeout 240 "${services[@]}"
printf 'update_complete revision=%s mode=%s\n' "$revision" "$mode"
