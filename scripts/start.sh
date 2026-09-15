#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
[[ "${1:-mock}" == mock ]] || fail 'Usage: bash scripts/start.sh mock [--create-only]'
[[ $# -le 2 && "${2:-}" == "${2:+--create-only}" ]] || fail 'Usage: bash scripts/start.sh mock [--create-only]'
require_env
require_engine
require_restart_policy
compose config --quiet
if [[ "${2:-}" == --create-only ]]; then
  compose create --build
  echo 'Containers created and left stopped.'
  exit 0
fi
require_free_app_port
compose up -d --build --wait --wait-timeout 180
compose port api 8000 | while IFS= read -r address; do echo "MuseForge foundation: http://$address"; done
