#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
require_engine
ensure_dirs

if [[ ! -e "$DEPLOY_ENV_FILE" ]]; then
  workspace_id="$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen)"
  db_password="$(openssl rand -hex 24)"
  broker_password="$(openssl rand -hex 24)"
  cat > "$DEPLOY_ENV_FILE" <<EOF
APP_PORT=${APP_PORT:-8000}
APP_BIND=127.0.0.1
POSTGRES_USER=museforge
POSTGRES_PASSWORD=$db_password
POSTGRES_DB=museforge
RABBITMQ_DEFAULT_USER=museforge
RABBITMQ_DEFAULT_PASS=$broker_password
DATABASE_URL=postgresql+psycopg://museforge:$db_password@db:5432/museforge
BROKER_URL=amqp://museforge:$broker_password@broker:5672//
WORKSPACE_ID=$workspace_id
ARTIFACT_ROOT=/var/lib/museforge/artifacts
WEB_DIST=/app/web
LYRICS_PROVIDER=mock
MUSIC_PROVIDER=mock
MOCK_QUEUE=museforge.mock.v1
YUE2_QUEUE=museforge.yue2.v1
QUARANTINE_QUEUE=museforge.quarantine.v1
LOG_LEVEL=INFO
WEIGHTS_DIR=/var/lib/museforge/weights
CACHE_DIR=/var/cache/museforge
DEVICE=cpu
PRECISION=float32
WORKER_CONCURRENCY=1
DURATION_SECONDS=8
DISPATCHER_POLL_SECONDS=1
RECONCILIATION_SECONDS=5
OUTBOX_CLAIM_SECONDS=15
BROKER_TIMEOUT_SECONDS=5
UNCLAIMED_SECONDS=60
QUEUE_DEADLINE_SECONDS=1800
HEARTBEAT_SECONDS=5
LEASE_SECONDS=90
ATTEMPT_DEADLINE_SECONDS=900
HARD_WATCHDOG_SECONDS=930
CANCELLATION_GRACE_SECONDS=20
MAX_ATTEMPTS=3
ORPHAN_GRACE_SECONDS=86400
EOF
  chmod 600 "$DEPLOY_ENV_FILE"
  echo "created private deployment environment: $DEPLOY_ENV_FILE"
else
  chmod 600 "$DEPLOY_ENV_FILE"
  echo "preserved existing deployment environment: $DEPLOY_ENV_FILE"
fi

export DEPLOY_ENV_FILE
write_mode_env mock
compose_with_mode mock config --quiet
if docker volume inspect musicgen-yue2-test_weights >/dev/null 2>&1; then
  echo 'verified shared YuE2 weights volume: musicgen-yue2-test_weights'
else
  echo 'warning: YuE2 weights volume is absent; real mode will fail preflight' >&2
fi
echo "deployment project: $PROJECT_NAME"
echo "application URL: http://127.0.0.1:$(grep '^APP_PORT=' "$DEPLOY_ENV_FILE" | cut -d= -f2)"
