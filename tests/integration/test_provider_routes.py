"""Broker and database routing checks; synthetic audio is not D03 acceptance."""
from datetime import datetime, timezone
import wave
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa

from museforge.db import schema as db
from museforge.domain import Generation, ProviderError
from museforge.jobs import submit
from museforge.dispatcher import publish
from museforge.routing import publisher_app
from museforge.worker.execution import execute
from museforge.worker.tasks import GenerationEnvelope, TASK_NAME


def real_settings(settings):
    return settings.model_copy(update=dict(music_provider='yue2', lyrics_provider='user',
        device='cuda', precision='bfloat16', model_id='test-model',
        model_revision='test-revision', decoder_revision='test-decoder', mock_test_enabled=False))


@pytest.mark.parametrize('provider', ['mock', 'yue2'])
@pytest.mark.parametrize('route', ['museforge.mock.v1', 'museforge.yue2.v1'])
def test_publisher_reaches_either_queue(settings, provider, route):
    configured = settings if provider == 'mock' else real_settings(settings)
    # Unknown IDs prevent this transport-only probe from claiming a real job.
    envelope = dict(schema_version=1, message_id=str(uuid4()), job_id=str(uuid4()),
        correlation_id=str(uuid4()), dispatch_sequence=1,
        dispatched_at=datetime.now(timezone.utc).isoformat(), provider_route=route)
    assert publish(envelope, configured)
    app = publisher_app(configured)
    try:
        with app.connection_for_read() as connection:
            with connection.channel() as channel:
                channel.queue_declare(queue=route, passive=True)
    finally:
        app.close()


def test_incompatible_worker_preserves_job_for_compatible_worker(settings, engine, monkeypatch):
    real = real_settings(settings)
    accepted = submit(engine, real, Generation(brief='Route isolation', instruments=['Guitar'], mood='Calm',
        lyrics={'mode': 'user', 'text': 'Exact retry checkpoint\n'}, duration_seconds=8), str(uuid4()))
    identifier = UUID(str(accepted['job_id']))
    with engine.connect() as connection:
        message = connection.execute(sa.select(db.outbox).where(db.outbox.c.job_id == identifier)).mappings().one()
        checkpoint = {'text': 'Previously checkpointed lyrics\n', 'source': 'user',
                      'provider_revision': '1', 'fixture_id': None, 'fixture_revision': None}
    with engine.begin() as connection:
        connection.execute(db.jobs.update().where(db.jobs.c.id == identifier).values(lyrics_checkpoint=checkpoint))
    envelope = GenerationEnvelope(schema_version=1, message_id=message['id'], job_id=identifier,
        correlation_id=message['correlation_id'], dispatch_sequence=1,
        dispatched_at=datetime.now(timezone.utc), provider_route=real.provider_route)
    for incompatible in (settings, real.model_copy(update={'model_revision': 'wrong'})):
        with pytest.raises(ProviderError, match='incompatible_envelope'):
            execute(incompatible, envelope)
        with engine.connect() as connection:
            job = connection.execute(sa.select(db.jobs).where(db.jobs.c.id == identifier)).mappings().one()
            assert job['state'] == 'queued' and job['attempt_count'] == 0 and job['error_code'] is None

    class SyntheticProvider:
        def __init__(self, config, output): self.output = output
        def generate(self, request, progress, cancel):
            assert request['lyrics']['text'] == checkpoint['text']
            with wave.open(str(self.output), 'wb') as audio:
                audio.setparams((2, 2, 48000, 0, 'NONE', 'not compressed'))
                audio.writeframes(b'\x01\x00\x01\x00' * 48000 * 6)
            return self.output
    monkeypatch.setattr('museforge.worker.execution.YuE2Music', SyntheticProvider)
    execute(real, envelope)
    with engine.connect() as connection:
        job = connection.execute(sa.select(db.jobs).where(db.jobs.c.id == identifier)).mappings().one()
        assert job['state'] == 'succeeded' and job['attempt_count'] == 1
        version = connection.execute(sa.select(db.versions).where(db.versions.c.id == job['result_version_id'])).mappings().one()
        assert version['lyrics'] == checkpoint['text']


def test_readiness_ignores_incompatible_registrations(settings, engine):
    from museforge.api.routes import readiness
    real = real_settings(settings).model_copy(update={'model_id': 'readiness-' + str(uuid4())})
    with engine.begin() as connection:
        connection.execute(db.registrations.insert().values(workspace_id=settings.workspace_id,
            worker_name='route-test-' + str(uuid4()), provider_id='yue2',
            provider_revision=real.provider_revision, model_id=real.model_id, model_revision='wrong',
            provider_route=real.provider_route, capability_revision=real.provider_revision,
            readiness='ready', last_heartbeat=sa.func.now(),
            expires_at=sa.func.now() + sa.text("interval '30 seconds'")))
        assert readiness(connection, real)['state'] == 'offline'
