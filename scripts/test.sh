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
  release)
    fail 'Full release acceptance belongs to Phase 06. Use unit, integration, or e2e for implementation checks.'
    ;;
  *) fail 'Usage: bash scripts/test.sh unit|integration|e2e|release' ;;
esac
