#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
mode="${1:-real}"
[[ "$mode" == real || "$mode" == mock ]] || fail 'Usage: bash scripts/start.sh [real|mock] [--create-only]'
[[ $# -le 2 && "${2:-}" == "${2:+--create-only}" ]] || fail 'Usage: bash scripts/start.sh [real|mock] [--create-only]'
require_env
require_engine
require_restart_policy
compose_with_mode "$mode" config --quiet
if [[ "${2:-}" == --create-only ]]; then
  compose_with_mode "$mode" create --build
  echo 'Containers created and left stopped.'
  exit 0
fi
require_free_app_port
compose_with_mode "$mode" up -d --build --wait --wait-timeout 240
compose_with_mode "$mode" port api 8000 | while IFS= read -r address; do echo "MuseForge $mode provider: http://$address"; done
