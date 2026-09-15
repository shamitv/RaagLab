#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
DEFAULT_PROJECT_NAME=museforge-managed
DEPLOY_ROOT="${MUSEFORGE_DEPLOY_ROOT:-$DATA_HOME/museforge-managed}"
PROJECT_NAME="${MUSEFORGE_PROJECT_NAME:-$DEFAULT_PROJECT_NAME}"
YUE2_WEIGHTS_VOLUME="${MUSEFORGE_YUE2_WEIGHTS_VOLUME:-museforge-yue2-weights}"
DEPLOY_ENV_FILE="$DEPLOY_ROOT/.env"
EVIDENCE_ROOT="${MUSEFORGE_EVIDENCE_ROOT:-$DEPLOY_ROOT/evidence}"
BACKUP_ROOT="${MUSEFORGE_BACKUP_ROOT:-$DEPLOY_ROOT/backups}"
export DEPLOY_ENV_FILE
export MUSEFORGE_YUE2_WEIGHTS_VOLUME="$YUE2_WEIGHTS_VOLUME"
COMPOSE_BASE=(docker compose --project-name "$PROJECT_NAME" --env-file "$DEPLOY_ENV_FILE" --profile mock --profile yue2
  -f "$ROOT/compose.yaml" -f "$ROOT/deploy/compose/compose.managed.yaml")

fail() { echo "deploy_error: $*" >&2; exit 1; }
require_env() { [[ -r "$DEPLOY_ENV_FILE" ]] || fail "missing $DEPLOY_ENV_FILE; run scripts/deploy/setup.sh"; }
require_engine() {
  command -v docker >/dev/null || fail 'Docker is unavailable; run inside the selected Linux/WSL environment.'
  local compose_version
  compose_version="$(docker compose version --short 2>/dev/null)" || fail 'Docker Compose v2 is required.'
  compose_version="${compose_version#v}"
  [[ "$(printf '%s\n' 2.24.4 "$compose_version" | sort -V | head -n 1)" == 2.24.4 ]] || fail 'Docker Compose >= 2.24.4 is required.'
  docker info --format '{{.OSType}}' 2>/dev/null | grep -qx linux || fail 'The selected Docker engine must run Linux containers.'
}
compose() { "${COMPOSE_BASE[@]}" "$@"; }
configured_yue2_device() {
  if [[ -n "${YUE2_DEVICE:-}" ]]; then
    printf '%s\n' "$YUE2_DEVICE"
    return
  fi
  if [[ -r "$DEPLOY_ROOT/.mode.env" ]]; then
    local saved
    saved="$(awk -F= '$1 == "YUE2_DEVICE" { value=$2 } END { if (value != "") print value }' "$DEPLOY_ROOT/.mode.env")"
    printf '%s\n' "${saved:-auto}"
    return
  fi
  printf '%s\n' auto
}
host_gpu_runtime_available() {
  local runtimes
  runtimes="$(docker info --format '{{json .Runtimes}}' 2>/dev/null || true)"
  [[ "$runtimes" == *nvidia* ]]
}
mode_compose() {
  local mode="${1:?mode mock or real}"; shift
  case "$mode" in
    mock) compose --profile mock "$@" ;;
    real)
      local device
      device="$(configured_yue2_device)"
      [[ "$device" == auto || "$device" == cpu || "$device" == cuda ]] || fail "YUE2_DEVICE must be auto, cpu, or cuda"
      local files=("$ROOT/compose.yue2.yaml" "$ROOT/deploy/compose/compose.managed.yue2.yaml")
      if [[ "$device" == cuda ]] || { [[ "$device" == auto ]] && host_gpu_runtime_available; }; then
        files+=("$ROOT/compose.yue2.gpu.yaml")
      fi
      if ((${#files[@]} == 3)); then
        compose --profile yue2 -f "${files[0]}" -f "${files[1]}" -f "${files[2]}" "$@"
      else
        compose --profile yue2 -f "${files[0]}" -f "${files[1]}" "$@"
      fi
      ;;
    *) fail "unknown mode: $mode" ;;
  esac
}
mode_services() {
  case "${1:?mode}" in
    mock) echo 'api dispatcher worker-mock' ;;
    real) echo 'api dispatcher worker-yue2' ;;
    *) fail "unknown mode: $1" ;;
  esac
}
deployment_env() {
  set -a
  # shellcheck disable=SC1090
  source "$DEPLOY_ENV_FILE"
  set +a
}
write_mode_env() {
  local mode="${1:?mode}"
  local saved_device=""
  if [[ -r "$DEPLOY_ROOT/.mode.env" ]]; then
    saved_device="$(awk -F= '$1 == "YUE2_DEVICE" { value=$2 } END { print value }' "$DEPLOY_ROOT/.mode.env")"
  fi
  deployment_env
  local requested_device="${YUE2_DEVICE:-${saved_device:-auto}}"
  # Start from the private base environment, removing every generated mode key
  # so repeated mode switches cannot accumulate conflicting assignments.
  local mode_tmp="$DEPLOY_ROOT/.mode.env.tmp"
  awk -F= '!($1 ~ /^(MUSIC_PROVIDER|LYRICS_PROVIDER|DEVICE|PRECISION|MODEL_ID|MODEL_REVISION|DECODER_REVISION|YUE2_DEVICE|YUE2_TEST_SMOKE|YUE2_CPU_THREADS|YUE2_MODEL_DIR|YUE2_VAE_DIR|YUE2_MEMORY_BUDGET_GIB|YUE2_PROCESS_TIMEOUT_SECONDS|YUE2_WARMUP_TIMEOUT_SECONDS|YUE2_OFFLOAD_AR|WORKER_CONCURRENCY|ATTEMPT_DEADLINE_SECONDS|HARD_WATCHDOG_SECONDS|QUEUE_DEADLINE_SECONDS)$/) { print }' "$DEPLOY_ENV_FILE" > "$mode_tmp"
  mv -f "$mode_tmp" "$DEPLOY_ROOT/.mode.env"
  if [[ "$mode" == real ]]; then
    [[ "$requested_device" == auto || "$requested_device" == cpu || "$requested_device" == cuda ]] || fail 'YUE2_DEVICE must be auto, cpu, or cuda'
    export MUSIC_PROVIDER=yue2 LYRICS_PROVIDER=user DEVICE="$requested_device" PRECISION=bfloat16
    export MODEL_ID=m-a-p/YuE2-3B MODEL_REVISION=29b3558dd46954a0cd9021dc76d5c91864a0f1c7
    export DECODER_REVISION=9a94e1d0ea9f8087e98f77fa88df4a4068104d2a
    export YUE2_DEVICE="$requested_device" YUE2_TEST_SMOKE=false YUE2_CPU_THREADS="${YUE2_CPU_THREADS:-4}"
    export YUE2_MODEL_DIR=/weights/model YUE2_VAE_DIR=/weights/vae
    export YUE2_MEMORY_BUDGET_GIB=16 YUE2_PROCESS_TIMEOUT_SECONDS=3600 YUE2_WARMUP_TIMEOUT_SECONDS=900
    export YUE2_OFFLOAD_AR=false WORKER_CONCURRENCY=1 ATTEMPT_DEADLINE_SECONDS=3600 HARD_WATCHDOG_SECONDS=3660 QUEUE_DEADLINE_SECONDS=1800
    cat >> "$DEPLOY_ROOT/.mode.env" <<EOF
MUSIC_PROVIDER=$MUSIC_PROVIDER
LYRICS_PROVIDER=$LYRICS_PROVIDER
DEVICE=$DEVICE
PRECISION=$PRECISION
MODEL_ID=$MODEL_ID
MODEL_REVISION=$MODEL_REVISION
DECODER_REVISION=$DECODER_REVISION
YUE2_DEVICE=$YUE2_DEVICE
YUE2_TEST_SMOKE=$YUE2_TEST_SMOKE
YUE2_CPU_THREADS=$YUE2_CPU_THREADS
YUE2_MODEL_DIR=$YUE2_MODEL_DIR
YUE2_VAE_DIR=$YUE2_VAE_DIR
YUE2_MEMORY_BUDGET_GIB=$YUE2_MEMORY_BUDGET_GIB
YUE2_PROCESS_TIMEOUT_SECONDS=$YUE2_PROCESS_TIMEOUT_SECONDS
YUE2_WARMUP_TIMEOUT_SECONDS=$YUE2_WARMUP_TIMEOUT_SECONDS
YUE2_OFFLOAD_AR=$YUE2_OFFLOAD_AR
WORKER_CONCURRENCY=$WORKER_CONCURRENCY
ATTEMPT_DEADLINE_SECONDS=$ATTEMPT_DEADLINE_SECONDS
HARD_WATCHDOG_SECONDS=$HARD_WATCHDOG_SECONDS
QUEUE_DEADLINE_SECONDS=$QUEUE_DEADLINE_SECONDS
EOF
  else
    cat >> "$DEPLOY_ROOT/.mode.env" <<'EOF'
MUSIC_PROVIDER=mock
LYRICS_PROVIDER=mock
DEVICE=cpu
PRECISION=float32
YUE2_DEVICE=cpu
EOF
  fi
  chmod 600 "$DEPLOY_ROOT/.mode.env"
}
compose_with_mode() {
  local mode="${1:?mode}"; shift
  mode_compose "$mode" --env-file "$DEPLOY_ROOT/.mode.env" "$@"
}
ensure_dirs() { mkdir -p "$DEPLOY_ROOT" "$EVIDENCE_ROOT" "$BACKUP_ROOT"; chmod 700 "$DEPLOY_ROOT" "$EVIDENCE_ROOT" "$BACKUP_ROOT"; }
stop_other_worker() {
  local mode="${1:?mode}"
  local other_service=worker-mock
  [[ "$mode" == mock ]] && other_service=worker-yue2
  local containers
  containers="$(docker ps -q --filter "label=com.docker.compose.project=$PROJECT_NAME" --filter "label=com.docker.compose.service=$other_service")"
  [[ -z "$containers" ]] || docker stop --time 30 $containers >/dev/null
}
