#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
set -euo pipefail
mode="${1:-real}"
[[ "$mode" == real ]] || fail 'recovery checks run against the integrated real deployment; use verify.sh mock for repeatable mock faults'
require_env; require_engine; write_mode_env real; deployment_env
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
evidence="$EVIDENCE_ROOT/$stamp-recovery"
mkdir -p "$evidence"; chmod 700 "$evidence"
worker="$(docker ps -q --filter "label=com.docker.compose.project=$PROJECT_NAME" --filter label=com.docker.compose.service=worker-yue2 | head -n 1)"
[[ -n "$worker" ]] || fail 'real worker is not running'
docker stop --time 5 "$worker" >/dev/null
python3 - "$APP_PORT" "$evidence/queued-cancellation.json" <<'PY'
import json, sys, time, uuid
from urllib.request import Request, urlopen
base = f'http://127.0.0.1:{sys.argv[1]}'
out = sys.argv[2]
body = {'brief':'D04 queued cancellation checkpoint','instruments':['Guitar'],'mood':'Calm','genre':'Folk','language':'English','duration_seconds':8,'lyrics':{'mode':'user','text':'[Verse]\nQueued cancellation checkpoint\n'}}
def request(path, method='GET', data=None):
    req = Request(base + path, method=method, data=data, headers={'Content-Type':'application/json','Idempotency-Key':str(uuid.uuid4())} if data else {})
    with urlopen(req, timeout=20) as response: return json.load(response)
accepted = request('/api/v1/generations', 'POST', json.dumps(body).encode())
cancelled = request(f"/api/v1/jobs/{accepted['job_id']}/cancel", 'POST')
deadline = time.time() + 30
while time.time() < deadline:
    current = request(accepted['status_url'])
    if current['state'] in ('cancelled','failed','timed_out'): break
    time.sleep(1)
else: raise SystemExit('queued cancellation did not reach a terminal state')
assert current['state'] == 'cancelled', current
json.dump({'accepted':accepted,'cancel_request':cancelled,'terminal':current}, open(out,'w'), indent=2)
PY
compose_with_mode real up -d --wait --wait-timeout 240 worker-yue2
echo "queued_cancellation_passed evidence=$evidence/queued-cancellation.json"
