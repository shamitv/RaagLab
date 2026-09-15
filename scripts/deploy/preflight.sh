#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
mode="${1:-mock}"
[[ "$mode" == mock || "$mode" == real ]] || fail 'usage: preflight.sh mock|real'
require_env; require_engine; ensure_dirs
write_mode_env "$mode"
compose_with_mode "$mode" config --quiet
deployment_env
port="${APP_PORT:-8000}"
if command -v ss >/dev/null && ss -H -ltn "sport = :$port" | grep -q .; then
  if ! docker ps --format '{{.Ports}}' | grep -q "127.0.0.1:${port}->"; then
    fail "APP_PORT $port is already in use; choose another port or stop only project $PROJECT_NAME"
  fi
fi
if [[ "$mode" == real ]]; then
  docker volume inspect "$YUE2_WEIGHTS_VOLUME" >/dev/null 2>&1 || fail "real mode requires weights volume $YUE2_WEIGHTS_VOLUME"
  compose_with_mode real config --quiet
fi
printf 'preflight_passed mode=%s project=%s port=%s evidence=%s\n' "$mode" "$PROJECT_NAME" "$port" "$EVIDENCE_ROOT"
