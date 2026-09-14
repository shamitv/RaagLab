"""Isolated Phase 2 service checkpoint, with optional browser evidence."""
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import uuid

ROOT=Path(__file__).resolve().parents[1]
prefix=os.environ.get('MUSEFORGE_TEST_PROJECT_PREFIX','museforge-phase2-test-')
project=prefix+uuid.uuid4().hex[:12]
env=dict(os.environ, APP_PORT='0')
base=['docker','compose','--project-name',project,'--env-file','.env','--profile','mock','-f','compose.yaml','-f','compose.test.yaml']
evidence=ROOT/'test-results'/project
evidence.mkdir(parents=True,exist_ok=True)


def run(*args, capture=False, timeout=600):
    result=subprocess.run([*base,*args],cwd=ROOT,env=env,check=False,text=True,stdout=subprocess.PIPE if capture else None,timeout=timeout)
    if result.returncode and capture:
        (evidence/'failed-command.txt').write_text(result.stdout)
        print(result.stdout)
    result.check_returncode()
    return result.stdout if capture else None


def get(path):
    with urllib.request.urlopen(origin+path,timeout=10) as response: return json.load(response)

try:
    run('build','api','dispatcher','worker-mock','tests',timeout=1800)
    if os.environ.get('PHASE4_BROWSER')=='1':
        run('build','browser-tests',timeout=1800)
    if prefix.startswith('museforge-phase4-test-'):
        run('up','-d','--scale','worker-mock=2','--wait','--wait-timeout','180','api','dispatcher','worker-mock')
    else:
        run('up','-d','--wait','--wait-timeout','180','api','dispatcher','worker-mock')
    origin='http://'+run('port','api','8000',capture=True).strip()
    run('run','--rm','tests','/app/.venv/bin/pytest','tests/unit')
    output=run('run','--rm','tests',capture=True)
    (evidence/'integration.txt').write_text(output)
    if os.environ.get('PHASE4_BROWSER')=='1':
        browser=run('run','--rm','-e',f'PLAYWRIGHT_OUTPUT_DIR=/test-results/{project}/browser',
                    'browser-tests',capture=True,timeout=1200)
        (evidence/'browser.txt').write_text(browser)
    # Hold a dedicated worker: accepted work survives API restart while queued.
    run('stop','worker-mock')
    body=json.dumps({'brief':'Queued restart checkpoint','instruments':['Piano'],'mood':'Calm',
                     'lyrics':{'mode':'user','text':'[Verse]\nA durable original song\n'},'duration_seconds':5}).encode()
    key=str(uuid.uuid4())
    request=urllib.request.Request(origin+'/api/v1/generations',data=body,
        headers={'Content-Type':'application/json','Idempotency-Key':key})
    started=time.monotonic()
    with urllib.request.urlopen(request,timeout=10) as response:
        assert response.status==202
        accepted=json.load(response)
    latency=time.monotonic()-started
    assert latency<1
    queued=get(accepted['status_url'])
    assert queued['state']=='queued'
    # Confirm accepted and completed records survive independent API restart.
    before=get('/api/v1/projects?limit=100')
    origin_before_restart=origin
    run('restart','api')
    # Docker may allocate a new ephemeral host port when the container restarts.
    origin='http://'+run('port','api','8000',capture=True).strip()
    request=urllib.request.Request(origin+'/api/v1/generations',data=body,
        headers={'Content-Type':'application/json','Idempotency-Key':key})
    deadline=time.monotonic()+60
    while True:
        try:
            after=get('/api/v1/projects?limit=100')
            break
        except Exception:
            if time.monotonic()>deadline: raise
            time.sleep(.5)
    assert before==after
    still_queued=get(accepted['status_url'])
    assert still_queued['state']=='queued' and still_queued['id']==queued['id']
    with urllib.request.urlopen(request,timeout=10) as response:
        assert json.load(response)['job_id']==accepted['job_id']
    run('up','-d','--wait','worker-mock')
    deadline=time.monotonic()+60
    while True:
        completed=get(accepted['status_url'])
        if completed['state'] in ('succeeded','failed','cancelled','timed_out'): break
        assert time.monotonic()<deadline
        time.sleep(.5)
    assert completed['state']=='succeeded' and completed['attempt_count']==1
    (evidence/'queued-restart.json').write_text(json.dumps({'acceptance_seconds':latency,
        'accepted':accepted,'before_restart':queued,'after_restart':still_queued,'completed':completed},indent=2))
    for item in after['items']:
        detail=get('/api/v1/projects/'+item['id'])
        if detail['active_version_id']:
            version=get('/api/v1/versions/'+detail['active_version_id'])
            with urllib.request.urlopen(origin+version['audio']['url'],timeout=10) as response:
                assert len(response.read())==version['audio']['byte_size']
    (evidence/'restart.json').write_text(json.dumps({'projects_preserved':len(after['items']), 'origin_before':origin_before_restart, 'origin_after':origin}))
    subprocess.run(['python3','scripts/demo.py','smoke','--base-url',origin],cwd=ROOT,check=True,timeout=120)
    if os.environ.get('PHASE2_BROWSER')=='1':
        subprocess.run(['npm','run','test:browser'],cwd=ROOT/'apps/web',env=dict(os.environ,API_BASE_URL=origin),check=True,timeout=600)
    (evidence/'readiness.json').write_text(json.dumps(get('/health/ready'),indent=2))
    phase='Phase 4' if prefix.startswith('museforge-phase4-test-') else 'Phase 2'
    print(f'{phase} service checks passed. Evidence: {evidence}')
finally:
    try:
        (evidence/'services.log').write_text(run('logs','--no-color',capture=True,timeout=30))
    finally:
        assert project.startswith(('museforge-phase2-test-','museforge-phase4-test-'))
        run('down','--volumes','--remove-orphans',timeout=120)
