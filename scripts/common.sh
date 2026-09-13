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
compose() { docker compose --env-file .env --profile mock "$@"; }
