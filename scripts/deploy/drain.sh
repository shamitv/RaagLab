#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
mode="${1:-real}"
require_env; require_engine; write_mode_env "$mode"; deployment_env
timeout_seconds="${DRAIN_TIMEOUT_SECONDS:-180}"
compose_with_mode "$mode" stop --timeout 30 dispatcher
deadline=$(( $(date +%s) + timeout_seconds ))
while :; do
  running="$(compose_with_mode "$mode" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atqc "select count(*) from jobs where state in ('running','cancellation_requested');" 2>/dev/null || true)"
  [[ "$running" =~ ^[0-9]+$ ]] || running=0
  if [[ "$running" == 0 ]]; then
    compose_with_mode "$mode" stop --timeout 120 "$(mode_services "$mode" | awk '{print $3}')"
    echo "drain_complete mode=$mode"
    exit 0
  fi
  (( $(date +%s) < deadline )) || fail "drain timed out with $running active jobs; workers remain running"
  sleep 2
done
