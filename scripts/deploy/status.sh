#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
require_env; require_engine
compose ps
deployment_env
if command -v curl >/dev/null; then
  curl --fail --silent --show-error "http://127.0.0.1:${APP_PORT:-8000}/api/v1/capabilities" || true
  echo
fi
