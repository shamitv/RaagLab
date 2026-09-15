#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
require_env; require_engine
compose stop --timeout "${STOP_TIMEOUT_SECONDS:-120}"
echo "stopped $PROJECT_NAME; named volumes were preserved"
