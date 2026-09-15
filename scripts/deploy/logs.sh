#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
require_env; require_engine
compose logs --tail="${LOG_LINES:-200}" --timestamps "${@:---no-log-prefix}"
