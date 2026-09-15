#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
mode="${1:-mock}"
require_env; require_engine; write_mode_env "$mode"; ensure_dirs
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
evidence="$EVIDENCE_ROOT/$stamp-$mode"
mkdir -p "$evidence"; chmod 700 "$evidence"
if [[ "$mode" == mock ]]; then
  MUSEFORGE_TEST_PROJECT_PREFIX="museforge-ubuntu1-d02-" PHASE4_BROWSER=1 python3 "$ROOT/scripts/verify-phase4.py" | tee "$evidence/phase4.log"
else
  compose_with_mode real run --rm --no-deps \
    --user 0 \
    -e D03_API_BASE=http://api:8000 -e D03_EVIDENCE_DIR=/evidence \
    -v "$ROOT/scripts:/verification:ro" -v "$evidence:/evidence" \
    worker-yue2 python /verification/verify-d03.py --expected-device cuda | tee "$evidence/d04-real.log"
fi
printf 'verification_complete mode=%s evidence=%s\n' "$mode" "$evidence"
