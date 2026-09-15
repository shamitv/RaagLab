"""Verify one real durable application job on a running isolated D03 stack.

Run in the dispatcher container with D03_API_BASE=http://api:8000 and an
evidence directory mounted at D03_EVIDENCE_DIR. Does not create model fixtures
or fall back to mock. Browser verification is a separate Playwright check.
"""
import hashlib
import argparse
from datetime import datetime
import io
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen
from uuid import UUID, uuid4
import wave

import sqlalchemy as sa
from museforge.config import Settings
from museforge.db import schema as db
from museforge.db.connection import engine_for


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--readiness-only', action='store_true')
    parser.add_argument('--expected-device', choices=['cpu', 'cuda'])
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    settings = Settings()
    assert settings.music_provider == 'yue2', 'Real provider configuration required'
    assert settings.yue2_test_smoke == args.smoke, 'Smoke mode must match the isolated stack'
    origin = os.environ.get('D03_API_BASE', 'http://api:8000')
    evidence = Path(os.environ.get('D03_EVIDENCE_DIR', '/tmp/d03-evidence'))
    evidence.mkdir(parents=True, exist_ok=True)

    def get(path, method='GET', headers=None):
        with urlopen(Request(origin + path, method=method, headers=headers or {}), timeout=30) as response:
            return response.status, dict(response.headers), response.read()

    def get_json(path):
        return json.loads(get(path)[2])

    if args.readiness_only:
        observations = []
        deadline = time.monotonic() + settings.yue2_warmup_timeout_seconds + 60
        while time.monotonic() < deadline:
            caps = get_json('/api/v1/capabilities')
            state = caps['readiness']['state']
            if not observations or observations[-1]['state'] != state:
                observations.append({'state': state, 'observed_at': time.time(),
                    'provider_id': caps['provider_id'], 'model_id': caps['model_id'],
                    'model_revision': caps['model_revision'], 'provider_route': caps['provider_route']})
            if state == 'ready': break
            time.sleep(.2)
        (evidence / 'readiness-transitions.json').write_text(json.dumps(observations, indent=2) + '\n')
        assert 'initializing' in [entry['state'] for entry in observations]
        assert observations[-1]['state'] == 'ready'
        print('Readiness transitioned through initializing to ready with real-provider metadata.')
        return

    # Container liveness is intentionally healthy during model warmup. Wait for
    # provider readiness separately before submitting the acceptance job.
    observations = []
    readiness_started = time.monotonic()
    deadline = time.monotonic() + settings.yue2_warmup_timeout_seconds + 60
    while True:
        caps = get_json('/api/v1/capabilities')
        observed = dict(caps['readiness'])
        if not observations or observations[-1] != observed:
            observations.append(observed)
        if observed['state'] in ('ready', 'busy'):
            break
        assert time.monotonic() < deadline, caps
        time.sleep(1)
    (evidence / 'readiness.json').write_text(json.dumps(observations, indent=2) + '\n')
    readiness_seconds = time.monotonic() - readiness_started
    assert caps['provider_id'] == 'yue2' and caps['readiness']['state'] in ('ready', 'busy'), caps
    lyrics = '[Verse]\nMorning light across the river\nEvery little moment shines\n\n[Chorus]\nCarry on together\nLet the music rise\n'
    request = dict(brief='A short warm acoustic folk song with a natural ending',
        instruments=['Guitar'], mood='Calm', language='English', genre='Folk', tempo='Medium',
        vocal_type='Instrumental', duration_seconds=8, seed=42, lyrics={'mode': 'user', 'text': lyrics})
    with urlopen(Request(origin + '/api/v1/generations', data=json.dumps(request).encode(),
            headers={'Content-Type': 'application/json', 'Idempotency-Key': str(uuid4())}), timeout=30) as response:
        assert response.status == 202
        accepted = json.load(response)
    (evidence / 'accepted.json').write_text(json.dumps(accepted, indent=2) + '\n')
    submitted_at = time.monotonic()
    deadline = time.monotonic() + settings.hard_watchdog_seconds + 120
    job = {}
    while time.monotonic() < deadline:
        job = get_json(accepted['status_url'])
        if job['state'] in ('succeeded', 'failed', 'timed_out', 'cancelled'):
            break
        time.sleep(2)
    (evidence / 'job.json').write_text(json.dumps(job, indent=2) + '\n')
    def timestamp(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00')).timestamp()
        except ValueError:
            return None

    queue_wait_seconds = None
    created_at = timestamp(job.get('created_at'))
    attempt_started = timestamp((job.get('attempts') or [{}])[0].get('started_at'))
    if created_at is not None and attempt_started is not None:
        queue_wait_seconds = max(0.0, attempt_started - created_at)
    (evidence / 'timing.json').write_text(json.dumps({
        'readiness_seconds': round(readiness_seconds, 3),
        'submit_to_terminal_seconds': round(time.monotonic() - submitted_at, 3),
        'queue_wait_seconds': queue_wait_seconds,
        'generation_elapsed_seconds': (job.get('attempts') or [{}])[0].get('elapsed_seconds'),
    }, indent=2) + '\n')
    assert job['state'] == 'succeeded', job
    assert job['attempt_count'] == 1 and len(job['attempts']) == 1
    version = get_json(job['version_url'])
    assert version['lyrics'] == lyrics
    provenance = version['provenance']
    for field, value in (('provider_id', 'yue2'), ('provider_revision', settings.provider_revision),
            ('model_id', settings.model_id), ('model_revision', settings.model_revision),
            ('decoder_revision', settings.decoder_revision), ('provider_route', settings.provider_route)):
        assert provenance[field] == value
    runtime = provenance['runtime']
    assert runtime['device'] in ('cpu', 'cuda')
    if args.expected_device:
        assert runtime['device'] == args.expected_device
        assert caps['readiness']['device'] == args.expected_device
    assert runtime['backend'] == ('torch' if runtime['device'] == 'cuda' else 'torch-eager')
    assert runtime['test_smoke'] == args.smoke
    if args.expected_device == 'cpu':
        expected_fallback = 'cuda_unavailable' if settings.device == 'auto' else None
        assert runtime['fallback_reason'] == expected_fallback
    elif args.expected_device == 'cuda':
        assert runtime['fallback_reason'] is None
    if runtime['device'] == 'cuda':
        assert runtime['gpu_resource']
    else:
        assert not runtime['gpu_resource']
    assert runtime['validation']['passed']
    if args.smoke:
        assert runtime['effective_settings']['cot'] == 'off'
        assert runtime['effective_settings']['semantic_sampling']['max_tokens'] == 32
        assert 0 < version['audio']['duration_seconds'] < 5
    else:
        assert version['audio']['duration_seconds'] > 5
    assert provenance['runtime']['requested_duration_seconds'] == 8
    status, headers, audio = get(version['audio']['url'])
    assert status == 200 and hashlib.sha256(audio).hexdigest() == version['audio']['sha256']
    with wave.open(io.BytesIO(audio)) as wav:
        assert (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) == (48000, 2, 2)
        assert wav.getnframes() / 48000 == version['audio']['duration_seconds']
    assert get(version['audio']['url'], 'HEAD')[0] == 200
    range_status, range_headers, part = get(version['audio']['url'], headers={'Range': 'bytes=0-43'})
    assert range_status == 206 and part == audio[:44]
    engine = engine_for(settings)
    try:
        with engine.connect() as connection:
            identifier = UUID(accepted['job_id'])
            assert connection.scalar(sa.select(sa.func.count()).select_from(db.versions).where(
                db.versions.c.generation_job_id == identifier)) == 1
            messages = connection.execute(sa.select(db.outbox).where(db.outbox.c.job_id == identifier)).mappings().all()
            assert len(messages) == 1 and messages[0]['state'] == 'published'
            assert messages[0]['provider_route'] == settings.yue2_queue
            registration = connection.execute(sa.select(db.registrations).where(
                db.registrations.c.id == UUID(job['attempts'][0]['worker_id']))).mappings().one()
            assert registration['provider_id'] == 'yue2'
            assert registration['runtime_metadata']['device'] == runtime['device']
            assert registration['runtime_metadata']['fallback_reason'] == runtime['fallback_reason']
            snapshot = connection.scalar(sa.select(db.jobs.c.execution_snapshot).where(db.jobs.c.id == identifier))
            assert snapshot['yue2_test_smoke'] == args.smoke
    finally:
        engine.dispose()
    (evidence / 'version.json').write_text(json.dumps(version, indent=2) + '\n')
    (evidence / 'artifact.wav').write_bytes(audio)
    print(json.dumps({'result': 'passed', 'project_id': accepted['project_id'],
                      'job_id': accepted['job_id'], 'version_id': version['id'],
                      'sample_rate': 48000, 'duration_seconds': version['audio']['duration_seconds']}, indent=2))


if __name__ == '__main__':
    main()
