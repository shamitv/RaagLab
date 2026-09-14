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


def submit_probe(brief, seed=None):
    body={'brief':brief,'instruments':['Piano'],'mood':'Calm',
          'lyrics':{'mode':'user','text':'[Verse]\nAn isolated recovery check\n'},'duration_seconds':5}
    if seed is not None: body['seed']=seed
    request=urllib.request.Request(origin+'/api/v1/generations',data=json.dumps(body).encode(),
        headers={'Content-Type':'application/json','Idempotency-Key':str(uuid.uuid4())})
    with urllib.request.urlopen(request,timeout=10) as response:
        assert response.status==202
        return json.load(response)


def wait_success(accepted, timeout=120):
    deadline=time.monotonic()+timeout
    while True:
        result=get(accepted['status_url'])
        if result['state'] in ('succeeded','failed','cancelled','timed_out'):
            assert result['state']=='succeeded', result
            return result
        assert time.monotonic()<deadline, f"Recovery job did not finish: {result}"
        time.sleep(.25)

try:
    run('build','api','dispatcher','worker-mock','tests',timeout=1800)
    if os.environ.get('PHASE4_BROWSER')=='1':
        run('build','browser-tests',timeout=1800)
    if prefix.startswith('museforge-phase4-test-'):
        run('up','-d','--scale','worker-mock=2','--wait','--wait-timeout','180','api','dispatcher','worker-mock')
    else:
        run('up','-d','--wait','--wait-timeout','180','api','dispatcher','worker-mock')
    origin='http://'+run('port','api','8000',capture=True).strip()
    browser_only=os.environ.get('PHASE4_BROWSER_ONLY')=='1'
    if not browser_only:
        # Services are already healthy; avoid Compose reconciling away the extra
        # worker replicas used by the phase-four concurrency coverage.
        run('run','--rm','--no-deps','tests','/app/.venv/bin/pytest','tests/unit')
        output=run('run','--rm','--no-deps','tests',capture=True)
        (evidence/'integration.txt').write_text(output)
    if os.environ.get('PHASE4_BROWSER')=='1':
        browser=run('run','--rm','--no-deps','-e',f'PLAYWRIGHT_OUTPUT_DIR=/test-results/{project}/browser',
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
    if prefix.startswith('museforge-phase4-test-'):
        # Exercise real dispatcher and broker restarts while accepting new work.
        run('restart','dispatcher')
        dispatcher_job=submit_probe('Phase four dispatcher restart')
        dispatcher_result=wait_success(dispatcher_job)
        (evidence/'dispatcher-restart.json').write_text(json.dumps({
            'accepted':dispatcher_job,'completed':dispatcher_result},indent=2))

        run('stop','broker')
        broker_job=submit_probe('Phase four broker outage recovery')
        before_broker=get(broker_job['status_url'])
        assert before_broker['state']=='queued', before_broker
        run('up','-d','--wait','--wait-timeout','180','broker')
        broker_result=wait_success(broker_job)
        (evidence/'broker-recovery.json').write_text(json.dumps({
            'queued_while_broker_stopped':before_broker,'accepted':broker_job,
            'completed':broker_result},indent=2))

        # Kill every mock worker while a deliberately slow job owns a lease.
        worker_job=submit_probe('Phase four worker loss recovery',seed=4294967203)
        deadline=time.monotonic()+30
        while True:
            worker_state=get(worker_job['status_url'])
            if worker_state['state']=='running': break
            assert time.monotonic()<deadline, f"Slow recovery job did not start: {worker_state}"
            time.sleep(.05)
        run('kill','--signal','SIGKILL','worker-mock')
        run('up','-d','--scale','worker-mock=2','--wait','--wait-timeout','180','worker-mock')
        worker_result=wait_success(worker_job,timeout=120)
        assert 2 <= worker_result['attempt_count'] <= 3, worker_result
        (evidence/'worker-loss.json').write_text(json.dumps({
            'last_observed_before_kill':worker_state,'accepted':worker_job,
            'completed_after_worker_recovery':worker_result},indent=2))

        # Stop/start runtime services without deleting their named volumes.
        before_full_restart=get('/api/v1/projects?limit=100')
        settings_before_restart=get('/api/v1/settings')
        run('stop')
        run('up','-d','--scale','worker-mock=2','--wait','--wait-timeout','180',
            'db','broker','api','dispatcher','worker-mock')
        origin='http://'+run('port','api','8000',capture=True).strip()
        deadline=time.monotonic()+60
        while True:
            try:
                after_full_restart=get('/api/v1/projects?limit=100')
                break
            except Exception:
                assert time.monotonic()<deadline, 'API did not return after full Compose restart'
                time.sleep(.5)
        settings_after_restart=get('/api/v1/settings')
        assert before_full_restart==after_full_restart
        assert settings_before_restart==settings_after_restart
        for item in after_full_restart['items']:
            detail=get('/api/v1/projects/'+item['id'])
            if detail['active_version_id']:
                version=get('/api/v1/versions/'+detail['active_version_id'])
                with urllib.request.urlopen(origin+version['audio']['url'],timeout=10) as response:
                    assert len(response.read())==version['audio']['byte_size']
        (evidence/'full-restart.json').write_text(json.dumps({
            'projects_preserved':len(after_full_restart['items']),
            'settings_revision':settings_after_restart['revision'],
            'active_audio_checked':True},indent=2))
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
