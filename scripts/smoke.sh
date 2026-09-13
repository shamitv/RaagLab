#!/usr/bin/env bash
set -euo pipefail
[[ "${1:-mock}" == mock ]] || { echo 'Usage: bash scripts/smoke.sh mock' >&2; exit 2; }
python3 "$(dirname -- "${BASH_SOURCE[0]}")/demo.py" smoke
