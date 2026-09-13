"""Real HTTP -> PostgreSQL -> confirmed RabbitMQ -> worker -> artifact proof."""
import hashlib
import io
import os
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4
import httpx
import pytest
import sqlalchemy as sa
from museforge.db import schema as db
from museforge.worker.app import app
from museforge.worker.tasks import TASK_NAME

BASE = os.environ.get('API_BASE_URL', 'http://api:8000')
TEXT = '  [अंतरा]\r\nहवा 🎵\n\n[பல்லவி]\nவானம்\t\n'


def submit(mode='user', seed=12, key=None, **changes):
    body = dict(brief='Original morning demo', instruments=['Piano', 'Tabla'], mood='Calm',
                lyrics={'mode': mode, 'text': TEXT if mode == 'user' else None}, seed=seed, duration_seconds=5) | changes
    started = time.monotonic()
    response = httpx.post(BASE+'/api/v1/generations', json=body, headers={'Idempotency-Key': key or str(uuid4())}, timeout=10)
    assert response.status_code == 202, response.text
    assert time.monotonic() - started < 1
    assert response.headers['location'] == response.json()['status_url']
    return response.json(), body


def wait(job, expected='succeeded'):
    deadline = time.monotonic() + 60
    states = []
    while time.monotonic() < deadline:
        response = httpx.get(BASE+job['status_url']); response.raise_for_status()
        result = response.json(); states.append(result['state'])
        if result['state'] in ('succeeded','failed','cancelled','timed_out'):
            assert result['state'] == expected, result
            return result, states
        time.sleep(.2)
    pytest.fail(f'Job did not finish: {states}')


@pytest.mark.parametrize('mode', ['user','static','mock'])
def test_complete_transport_and_audio(mode, engine):
    job, _ = submit(mode)
    result, states = wait(job)
    assert result['attempt_count'] == 1
    version = httpx.get(BASE+result['version_url']).json()
    assert version['provenance']['lyrics']['source'] == mode
    if mode == 'user': assert version['lyrics'] == TEXT
    audio = httpx.get(BASE+version['audio']['url'])
    assert audio.status_code == 200
    info = version['audio']
    assert hashlib.sha256(audio.content).hexdigest() == info['sha256']
    assert len(audio.content) == info['byte_size']
    with wave.open(io.BytesIO(audio.content)) as wav:
        assert wav.getframerate() == info['sample_rate'] == 44100
        assert wav.getnchannels() == info['channels'] == 2
        assert wav.getsampwidth() == 2
        assert wav.getnframes()/wav.getframerate() == info['duration_seconds'] == 5
        assert any(wav.readframes(wav.getnframes()))
    with engine.connect() as c:
        assert c.scalar(sa.select(sa.func.count()).select_from(db.versions).where(db.versions.c.generation_job_id == UUID(job['job_id']))) == 1
        message = c.execute(sa.select(db.outbox).where(db.outbox.c.job_id == UUID(job['job_id']))).mappings().one()
        assert message['state'] == 'published' and message['confirmed_at'] is not None
        checkpoint = c.scalar(sa.select(db.jobs.c.lyrics_checkpoint).where(db.jobs.c.id == UUID(job['job_id'])))
        assert checkpoint['text'] == version['lyrics']
    assert 'storage_key' not in str(version)


def test_concurrent_idempotency_conflict_and_duplicate_delivery(engine):
    key = str(uuid4())
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: submit(key=key)[0], range(4)))
    assert len({r['job_id'] for r in results}) == len({r['project_id'] for r in results}) == 1
    job = results[0]
    completed, _ = wait(job)
    _, body = submit(key=key)
    conflict = httpx.post(BASE+'/api/v1/generations', json=body | {'brief':'Different'}, headers={'Idempotency-Key':key})
    assert conflict.status_code == 409
    with engine.connect() as c:
        message = c.execute(sa.select(db.outbox).where(db.outbox.c.job_id == UUID(job['job_id']))).mappings().one()
        envelope = {k: str(message[k]) if k in ('job_id','correlation_id') else message[k] for k in ('job_id','correlation_id','dispatch_sequence','provider_route','schema_version')}
        envelope.update(message_id=str(message['id']), dispatched_at=message['confirmed_at'].isoformat())
    for _ in range(2): app.send_task(TASK_NAME,args=[envelope],task_id=envelope['message_id'],queue='museforge.mock.v1')
    time.sleep(2)
    after = httpx.get(BASE+job['status_url']).json()
    assert after['result_version_id'] == completed['result_version_id']
    assert after['attempt_count'] == 1


def test_project_isolation():
    first, _ = submit(seed=20)
    second, _ = submit(seed=21, lyrics={'mode':'user','text':'Second project\n'})
    one, _ = wait(first); two, _ = wait(second)
    versions = [httpx.get(BASE+j['version_url']).json() for j in (one,two)]
    assert versions[0]['project_id'] != versions[1]['project_id']
    assert [v['lyrics'] for v in versions] == [TEXT, 'Second project\n']
    assert versions[0]['audio']['sha256'] != versions[1]['audio']['sha256']


@pytest.mark.parametrize(('seed','state'), [(4294967201,'failed'),(4294967202,'timed_out'),(4294967204,'failed')])
def test_typed_failure_has_no_result(seed, state, engine):
    job, _ = submit(seed=seed)
    result, _ = wait(job,state)
    assert result['result_version_id'] is None
    assert result['attempt_count'] == (3 if seed == 4294967204 else 1)
    with engine.connect() as c:
        assert c.scalar(sa.select(sa.func.count()).select_from(db.versions).where(db.versions.c.generation_job_id==UUID(job['job_id']))) == 0


def test_running_and_queued_cancellation():
    running, _ = submit(seed=4294967203)
    deadline = time.monotonic()+20
    while httpx.get(BASE+running['status_url']).json()['state'] != 'running':
        assert time.monotonic()<deadline
        time.sleep(.1)
    queued, _ = submit()
    response = httpx.post(BASE+queued['status_url']+'/cancel')
    assert response.status_code == 200 and response.json()['state']=='cancelled'
    response = httpx.post(BASE+running['status_url']+'/cancel')
    assert response.status_code == 202
    result, _ = wait(running,'cancelled')
    assert result['result_version_id'] is None
    assert httpx.post(BASE+running['status_url']+'/cancel').json()['state']=='cancelled'


def test_artifact_ranges_and_missing(engine):
    job, _ = submit()
    result, _ = wait(job)
    version = httpx.get(BASE+result['version_url']).json()
    url = BASE+version['audio']['url']; size = version['audio']['byte_size']
    head = httpx.head(url)
    assert head.status_code==200 and not head.content and int(head.headers['content-length'])==size
    assert head.headers['accept-ranges']=='bytes'
    for value, length in [('bytes=0-43',44),('bytes=-20',20), (f'bytes={size-12}-',12)]:
        response = httpx.get(url,headers={'Range':value})
        assert response.status_code==206 and len(response.content)==length
    response = httpx.get(url,headers={'Range':f'bytes={size}-'})
    assert response.status_code==416 and response.headers['content-range']==f'bytes */{size}'
    identifier = UUID(version['audio']['id'])
    with engine.begin() as c:
        key = c.scalar(sa.select(db.artifacts.c.storage_key).where(db.artifacts.c.id==identifier))
        c.execute(db.artifacts.update().where(db.artifacts.c.id==identifier).values(storage_key='../etc/passwd'))
    try:
        assert httpx.get(url).status_code==410
        assert httpx.get(BASE+result['version_url']).status_code==200
    finally:
        with engine.begin() as c: c.execute(db.artifacts.update().where(db.artifacts.c.id==identifier).values(storage_key=key))


def test_validation_and_resource_routes():
    assert httpx.post(BASE+'/api/v1/generations',content=b'x'*131073).status_code==413
    assert httpx.get(BASE+'/api/v1/projects?cursor=bad').status_code==422
    assert httpx.get(BASE+'/api/v1/projects/'+str(uuid4())).status_code==404
    project = httpx.post(BASE+'/api/v1/projects',json={'title':'Empty project'})
    assert project.status_code==201 and project.json()['active_version_id'] is None
    assert httpx.get(BASE+project.headers['location']).headers['etag']=='"1"'


def test_expired_fence_cannot_write_or_finalize(engine, settings):
    from museforge.jobs import lock_job, owned, now
    from museforge.domain import ProviderError
    from datetime import timedelta
    job, _ = submit(seed=4294967203)
    identifier = UUID(job['job_id'])
    deadline = time.monotonic()+20
    while httpx.get(BASE+job['status_url']).json()['state'] != 'running':
        assert time.monotonic()<deadline
        time.sleep(.1)
    with engine.begin() as c:
        _, current = lock_job(c,identifier,settings)
        with pytest.raises(ProviderError,match='lease_lost'): owned(c,current,current['fence_token']-1,settings)
        # Roll back the expired-lease injection after proving the publication predicate.
        transaction = c.begin_nested()
        c.execute(db.attempts.update().where(db.attempts.c.job_id==identifier).values(lease_expires_at=now(c)-timedelta(seconds=1)))
        with pytest.raises(ProviderError,match='lease_lost'): owned(c,current,current['fence_token'],settings)
        transaction.rollback()
    httpx.post(BASE+job['status_url']+'/cancel')
    wait(job,'cancelled')


def test_latest_submission_selection_is_fenced():
    first, _ = submit(seed=4294967203)
    second, _ = submit(project_id=first['project_id'])
    one, _ = wait(first)
    two, _ = wait(second)
    project = httpx.get(BASE+'/api/v1/projects/'+first['project_id']).json()
    assert project['active_version_id']==two['result_version_id']
    versions=httpx.get(BASE+'/api/v1/projects/'+first['project_id']+'/versions').json()['items']
    assert [v['number'] for v in versions]==[1,2]
    assert one['result_version_id'] != two['result_version_id']


def test_interrupted_outbox_claim_is_reclaimed(engine, settings):
    from contextlib import contextmanager
    from datetime import timedelta
    from museforge.jobs import submit as accept, now
    from museforge.domain import Generation
    with engine.begin() as c:
        class TransactionEngine:
            @contextmanager
            def begin(self): yield c
        job = accept(TransactionEngine(), settings, Generation(brief='Reclaimed publication', instruments=['Piano'], mood='Calm'),str(uuid4()))
        identifier=job['job_id']
        c.execute(db.outbox.update().where(db.outbox.c.job_id==identifier).values(state='publishing',
            claim_token=uuid4(),claim_expires_at=now(c)-timedelta(seconds=1),publication_count=1))
    result,_=wait(job)
    assert result['attempt_count']==1
    with engine.connect() as c:
        message=c.execute(sa.select(db.outbox).where(db.outbox.c.job_id==identifier)).mappings().one()
        assert message['state']=='published' and message['publication_count']>=2


def test_expired_execution_lease_recovers_checkpoint(engine, settings):
    from contextlib import contextmanager
    from datetime import timedelta
    from museforge.jobs import submit as accept, now
    from museforge.domain import Generation
    from museforge.providers import DemoLyrics
    with engine.begin() as c:
        class TransactionEngine:
            @contextmanager
            def begin(self): yield c
        job=accept(TransactionEngine(),settings,Generation(brief='Lease recovery',instruments=['Piano'],mood='Calm',
            lyrics={'mode':'user','text':TEXT}),str(uuid4()))
        identifier=job['job_id'];timestamp=now(c);worker=uuid4()
        snapshot=c.scalar(sa.select(db.jobs.c.execution_snapshot).where(db.jobs.c.id==identifier))
        checkpoint=DemoLyrics().generate(snapshot,lambda *_:None,lambda:None)
        c.execute(db.registrations.insert().values(id=worker,workspace_id=settings.workspace_id,worker_name=f'lost-{worker}',
            provider_id='mock',provider_revision='1',provider_route=settings.mock_queue,capability_revision='1',readiness='offline',
            last_heartbeat=timestamp-timedelta(seconds=60),expires_at=timestamp-timedelta(seconds=30)))
        c.execute(db.jobs.update().where(db.jobs.c.id==identifier).values(state='running',attempt_count=1,fence_token=1,
            attempt_deadline=timestamp+timedelta(seconds=60),lyrics_checkpoint=checkpoint))
        c.execute(db.attempts.insert().values(workspace_id=settings.workspace_id,job_id=identifier,worker_id=worker,
            attempt_number=1,fence_token=1,heartbeat_at=timestamp-timedelta(seconds=60),lease_expires_at=timestamp-timedelta(seconds=1)))
        c.execute(db.outbox.update().where(db.outbox.c.job_id==identifier).values(state='published',confirmed_at=timestamp))
    result,_=wait(job)
    assert result['attempt_count']==2
    assert httpx.get(BASE+result['version_url']).json()['lyrics']==TEXT
    with engine.connect() as c:
        assert c.scalar(sa.select(db.jobs.c.lyrics_checkpoint).where(db.jobs.c.id==identifier))==checkpoint


def test_config_defaults_are_snapshotted_once_on_idempotent_replay(engine, settings):
    from museforge.jobs import submit as accept
    from museforge.domain import Generation
    key=str(uuid4())
    request=Generation(brief='Configured defaults',instruments=['Piano'],mood='Calm')
    first=accept(engine,settings.model_copy(update={'lyrics_provider':'static','duration_seconds':5}),request,key)
    second=accept(engine,settings.model_copy(update={'lyrics_provider':'mock','duration_seconds':10}),request,key)
    assert first['job_id']==second['job_id']
    result,_=wait(first)
    version=httpx.get(BASE+result['version_url']).json()
    assert version['provenance']['lyrics']['source']=='static'
    assert version['audio']['duration_seconds']==5
