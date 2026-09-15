#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
mode="${1:-real}"
[[ "$mode" == real || "$mode" == mock ]] || fail 'Usage: bash scripts/setup.sh [real|mock]'
if [[ ! -e .env ]]; then
  (umask 077; set -o noclobber; cat .env.example > .env)
  if [[ "$mode" == real ]]; then
    sed -i \
      -e 's/^LYRICS_PROVIDER=.*/LYRICS_PROVIDER=user/' \
      -e 's/^MUSIC_PROVIDER=.*/MUSIC_PROVIDER=yue2/' \
      -e 's/^DEVICE=.*/DEVICE=auto/' \
      -e 's/^PRECISION=.*/PRECISION=bfloat16/' \
      -e 's/^# MODEL_ID=.*/MODEL_ID=m-a-p\/YuE2-3B/' \
      -e 's/^# MODEL_REVISION=.*/MODEL_REVISION=29b3558dd46954a0cd9021dc76d5c91864a0f1c7/' \
      -e 's/^# DECODER_REVISION=.*/DECODER_REVISION=9a94e1d0ea9f8087e98f77fa88df4a4068104d2a/' \
      -e 's/^QUEUE_DEADLINE_SECONDS=.*/QUEUE_DEADLINE_SECONDS=1800/' \
      -e 's/^ATTEMPT_DEADLINE_SECONDS=.*/ATTEMPT_DEADLINE_SECONDS=3600/' \
      -e 's/^HARD_WATCHDOG_SECONDS=.*/HARD_WATCHDOG_SECONDS=3660/' .env
    cat >> .env <<'EOF'
MUSEFORGE_YUE2_WEIGHTS_VOLUME=museforge-yue2-weights
YUE2_DEVICE=auto
YUE2_TEST_SMOKE=false
YUE2_CPU_THREADS=4
YUE2_MODEL_DIR=/weights/model
YUE2_VAE_DIR=/weights/vae
YUE2_RUNNER=/opt/yue2-test/generate.py
YUE2_PREFLIGHT=/opt/yue2-test/preflight.py
YUE2_MEMORY_BUDGET_GIB=16
YUE2_PROCESS_TIMEOUT_SECONDS=3600
YUE2_WARMUP_TIMEOUT_SECONDS=900
YUE2_OFFLOAD_AR=false
EOF
  fi
  echo "Created .env for the $mode provider."
else
  echo "Preserved existing .env; its configured provider remains unchanged."
fi
require_engine
compose_with_mode "$mode" config --quiet
echo "Prerequisites ready. Start with: bash scripts/start.sh $mode"
