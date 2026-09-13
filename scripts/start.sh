#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
[[ "${1:-mock}" == mock && $# -le 1 ]] || fail 'Usage: bash scripts/start.sh mock (real adapters are not implemented)'
require_env
require_engine
compose config --quiet
compose up -d --build --wait --wait-timeout 180
compose port api 8000 | while IFS= read -r address; do echo "MuseForge foundation: http://$address"; done
