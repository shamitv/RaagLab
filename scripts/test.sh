#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
case "${1:-}" in
  unit)
    command -v uv >/dev/null || fail 'Install uv 0.12.13 for local tests; see docs/development.md.'
    command -v npm >/dev/null || fail 'Node 24 and npm 11 are required for frontend tests.'
    uv sync --frozen --group api --group mock-worker
    uv run --frozen --group api --group mock-worker pytest tests/unit
    (cd apps/web; npm ci --no-audit --no-fund; npm run build; npm test)
    ;;
  integration)
    require_env
    require_engine
    MUSEFORGE_TEST_PROJECT_PREFIX=museforge-phase4-test- python3 scripts/verify-phase2.py
    ;;
  e2e)
    require_env
    require_engine
    python3 scripts/verify-phase4.py
    ;;
  yue2-cpu|yue2-gpu)
    require_env
    require_engine
    if [[ "$1" == yue2-gpu ]]; then
      python3 scripts/verify-yue2-devices.py --gpu
    else
      python3 scripts/verify-yue2-devices.py --cpu
    fi
    ;;
  release)
    require_engine
    shift
    python3 scripts/verify-release.py "$@"
    ;;
  *) fail 'Usage: bash scripts/test.sh unit|integration|e2e|yue2-cpu|yue2-gpu|release' ;;
esac
