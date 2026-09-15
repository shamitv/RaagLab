#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
fail() { echo "$*" >&2; exit 1; }
require_engine() {
  command -v docker >/dev/null || fail 'Docker is unavailable. Use a reachable Linux Docker engine and Compose v2 >= 2.24.4.'
  local version
  version="$(docker compose version --short)" || fail 'Install the Docker Compose v2 plugin (>= 2.24.4).'
  version="${version#v}"
  [[ "$(printf '%s\n' 2.24.4 "$version" | sort -V | head -n 1)" == 2.24.4 ]] || fail 'Compose >= 2.24.4 is required.'
  docker info >/dev/null 2>&1 || fail 'No reachable Linux Docker engine. Check your Docker context and permissions.'
  [[ "$(docker info --format '{{.OSType}}')" == linux ]] || fail 'The engine must run Linux containers.'
}
require_env() { [[ -f .env ]] || fail 'Run bash scripts/setup.sh first to initialize .env.'; }
env_value() { awk -F= -v key="$1" '$1 == key { value=$2 } END { print value }' .env; }
host_gpu_runtime_available() {
  docker info --format '{{json .Runtimes}}' 2>/dev/null | grep -q nvidia
}
compose_with_mode() {
  local mode="${1:?mode}"; shift
  case "$mode" in
    mock) docker compose --env-file .env --profile mock -f compose.yaml -f compose.mock.yaml "$@" ;;
    real)
      local device files=(compose.yaml compose.yue2.yaml)
      device="${YUE2_DEVICE:-$(env_value YUE2_DEVICE)}"; device="${device:-auto}"
      [[ "$device" == auto || "$device" == cpu || "$device" == cuda ]] || fail 'YUE2_DEVICE must be auto, cpu, or cuda.'
      if [[ "$device" == cuda ]] || { [[ "$device" == auto ]] && host_gpu_runtime_available; }; then files+=(compose.yue2.gpu.yaml); fi
      local args=(); for file in "${files[@]}"; do args+=(-f "$file"); done
      docker compose --env-file .env --profile yue2 "${args[@]}" "$@"
      ;;
    *) fail 'mode must be real or mock' ;;
  esac
}
configured_mode() { [[ "$(env_value MUSIC_PROVIDER)" == yue2 ]] && echo real || echo mock; }
compose() { compose_with_mode "$(configured_mode)" "$@"; }
require_restart_policy() {
  local saved policy
  saved="$(awk -F= '$1 == "CONTAINER_RESTART_POLICY" { print $2 }' .env | tail -n 1)"
  policy="${CONTAINER_RESTART_POLICY:-${saved:-unless-stopped}}"
  [[ "$policy" == unless-stopped || "$policy" == no ]] || fail 'CONTAINER_RESTART_POLICY must be unless-stopped or no.'
  export CONTAINER_RESTART_POLICY="$policy"
}
require_free_app_port() {
  local saved port owner own
  saved="$(awk -F= '$1 == "APP_PORT" { print $2 }' .env | tail -n 1)"
  port="${APP_PORT:-${saved:-8000}}"
  owner="$(docker ps --filter "publish=$port" --format '{{.Names}}' | head -n 1)"
  own="$(compose ps api --format '{{.Name}}' 2>/dev/null | head -n 1)"
  [[ -z "$owner" || "$owner" == "$own" ]] || fail "127.0.0.1:$port is already owned by container $owner. Set APP_PORT to another port."
}
