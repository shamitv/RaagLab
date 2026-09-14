"""Execution child lifecycle; all durable writes are fenced."""
import logging
import os
import socket
import tempfile
import threading
import time
from datetime import timedelta
from pathlib import Path
from uuid import uuid4
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from museforge.db import schema as db
from museforge.db.connection import engine_for
from museforge.domain import ProviderError, provider_capabilities
from museforge.jobs import lock_job, now, owned, finish_error
from museforge.providers import DemoLyrics, MockMusic, YuE2Music
from museforge.storage import publish

log = logging.getLogger('museforge')


def execute(settings, envelope):
    # Delivery compatibility is not a durable job outcome.
    if envelope.provider_route != settings.provider_route:
        raise ProviderError('incompatible_envelope')
    engine = engine_for(settings)
    fence = None
    temporary = None
    stop = threading.Event()
    lost = threading.Event()
    heartbeat = None
    worker_id = None
    try:
        with engine.begin() as c:
            _, job = lock_job(c, envelope.job_id, settings)
            if job['state'] not in ('queued', 'retrying') or job['dispatch_sequence'] != envelope.dispatch_sequence:
                return
            if envelope.provider_route != job['provider_route'] or envelope.correlation_id != job['correlation_id']:
                raise ProviderError('incompatible_envelope')
            message = c.execute(sa.select(db.outbox).where(db.outbox.c.id == envelope.message_id,
                db.outbox.c.job_id == job['id'], db.outbox.c.dispatch_sequence == envelope.dispatch_sequence)).mappings().first()
            if not message: raise ProviderError('incompatible_envelope')
            provider_snapshot = job['execution_snapshot'].get('providers', {})
            snapshot_revision = provider_snapshot.get('provider_revision', provider_snapshot.get('revision'))
            snapshot_route = provider_snapshot.get('route', settings.mock_queue if settings.provider_id == 'mock' else None)
            if (job['snapshot_schema_version'] != 1 or
                    provider_snapshot.get('music') != settings.provider_id or
                    snapshot_revision != settings.provider_revision or
                    snapshot_route != settings.provider_route or
                    provider_snapshot.get('model_id') != settings.model_id or
                    provider_snapshot.get('model_revision') != settings.model_revision or
                    provider_snapshot.get('decoder_revision') != settings.decoder_revision or
                    (settings.music_provider == 'yue2' and
                     job['execution_snapshot'].get('yue2_test_smoke', False) != settings.yue2_test_smoke) or
                    envelope.provider_route != settings.provider_route):
                raise ProviderError('incompatible_envelope')
            if settings.music_provider == 'yue2' and job['execution_snapshot'].get('operation') != 'generate':
                finish_error(c, job, settings, 'unsupported_capability')
                return
            timestamp = now(c)
            if job['next_action_at'] > timestamp: return
            limits = job['execution_snapshot']['limits']
            if job['queue_deadline'] <= timestamp:
                finish_error(c, job, settings, 'deadline_exceeded')
                return
            if job['attempt_count'] >= limits['max_attempts']:
                finish_error(c, job, settings, 'attempts_exhausted')
                return
            worker_id = uuid4()
            name = f'{socket.gethostname()}:{os.getpid()}'
            statement = insert(db.registrations).values(id=worker_id, workspace_id=settings.workspace_id, worker_name=name,
                provider_id=settings.provider_id, provider_revision=settings.provider_revision,
                model_id=settings.model_id, model_revision=settings.model_revision,
                provider_route=settings.provider_route, capability_revision=settings.provider_revision,
                readiness='busy', runtime_metadata=settings.runtime_metadata,
                last_heartbeat=timestamp, expires_at=timestamp + timedelta(seconds=limits['lease_seconds']))
            worker_id = c.scalar(statement.on_conflict_do_update(index_elements=['worker_name'], set_={
                'readiness': 'busy', 'last_heartbeat': timestamp, 'expires_at': statement.excluded.expires_at,
                'provider_id': statement.excluded.provider_id, 'provider_revision': statement.excluded.provider_revision,
                'model_id': statement.excluded.model_id, 'model_revision': statement.excluded.model_revision,
                'provider_route': statement.excluded.provider_route,
                'capability_revision': statement.excluded.capability_revision,
                'runtime_metadata': statement.excluded.runtime_metadata}).returning(db.registrations.c.id))
            fence = job['fence_token'] + 1
            c.execute(db.jobs.update().where(db.jobs.c.id == job['id']).values(state='running', stage='writing_lyrics',
                attempt_count=job['attempt_count'] + 1, fence_token=fence, error_code=None,
                attempt_deadline=timestamp + timedelta(seconds=limits['attempt_deadline_seconds'])))
            c.execute(db.attempts.insert().values(workspace_id=settings.workspace_id, job_id=job['id'], worker_id=worker_id,
                attempt_number=job['attempt_count'] + 1, fence_token=fence, heartbeat_at=timestamp,
                lease_expires_at=timestamp + timedelta(seconds=limits['lease_seconds'])))
        log.info('job_claimed job=%s message=%s correlation=%s fence=%s', job['id'], envelope.message_id, envelope.correlation_id, fence)

        def update(stage=None, checkpoint=None):
            if lost.is_set(): raise ProviderError('lease_lost')
            with engine.begin() as c:
                _, current = lock_job(c, job['id'], settings)
                timestamp = owned(c, current, fence, settings)
                expiry = timestamp + timedelta(seconds=limits['lease_seconds'])
                c.execute(db.attempts.update().where(db.attempts.c.job_id == job['id'], db.attempts.c.fence_token == fence)
                    .values(heartbeat_at=timestamp, lease_expires_at=expiry))
                c.execute(db.registrations.update().where(db.registrations.c.id == worker_id)
                    .values(last_heartbeat=timestamp, expires_at=expiry))
                values = {}
                if stage: values['stage'] = stage
                if checkpoint is not None and current['lyrics_checkpoint'] is None: values['lyrics_checkpoint'] = checkpoint
                if values: c.execute(db.jobs.update().where(db.jobs.c.id == job['id']).values(**values))
            if stage: log.info('job_stage job=%s fence=%s stage=%s', job['id'], fence, stage)

        def beat():
            while not stop.wait(limits['heartbeat_seconds']):
                try: update()
                except Exception:
                    lost.set()
                    return

        heartbeat = threading.Thread(target=beat, daemon=True)
        heartbeat.start()
        last_check = [0.0]
        def check():
            if lost.is_set(): raise ProviderError('lease_lost')
            if time.monotonic() - last_check[0] > .2:
                update()
                last_check[0] = time.monotonic()

        request = job['execution_snapshot']
        checkpoint = job['lyrics_checkpoint'] or DemoLyrics().generate(request, update, check)
        provider_request = dict(request, lyrics=dict(request['lyrics'], text=checkpoint['text']))
        update('composing_music', checkpoint)
        if settings.mock_test_enabled:
            scenario = request.get('_test', {})
            end = time.monotonic() + scenario.get('delay', settings.mock_test_delay_seconds)
            while time.monotonic() < end:
                check()
                time.sleep(.05)
            outcome = scenario.get('outcome', settings.mock_test_outcome)
            if outcome != 'success':
                raise ProviderError(outcome, outcome == 'transient_failure')
        reuse_audio = request['operation'] == 'lyrics_edit'
        if not reuse_audio:
            if settings.artifact_root.is_symlink(): raise ProviderError('artifact_unavailable')
            settings.artifact_root.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix=f'.{job["id"]}-{fence}-', suffix='.tmp', dir=settings.artifact_root)
            os.close(fd)
            temporary = Path(name)
            provider = MockMusic(temporary) if settings.music_provider == 'mock' else YuE2Music(settings, temporary)
            provider.generate(provider_request, update, check)
            update('validating_audio')
            artifact = publish(settings.artifact_root, temporary, job['id'], fence,
                               request['duration_seconds'] if settings.music_provider == 'mock' else None,
                               expected_sample_rate=44100 if settings.music_provider == 'mock' else 48000)
            provider_metadata = getattr(provider, 'metadata', {})
        else:
            provider_metadata = {}
        update('saving_result')
        with engine.begin() as c:
            project, current = lock_job(c, job['id'], settings)
            timestamp = owned(c, current, fence, settings)
            artifact_id, version_id = uuid4(), uuid4()
            if reuse_audio:
                artifact_id = c.scalar(sa.select(db.links.c.artifact_id).where(db.links.c.version_id == request['source_version_id'], db.links.c.role == 'audio'))
            else:
                c.execute(db.artifacts.insert().values(id=artifact_id, workspace_id=settings.workspace_id,
                    **artifact, published_at=timestamp, available_at=timestamp))
            c.execute(db.versions.insert().values(id=version_id, workspace_id=settings.workspace_id, project_id=project['id'],
                generation_job_id=job['id'], number=project['next_version_number'], label=f"Version {project['next_version_number']}",
                parent_version_id=request['source_version_id'], inputs=request, lyrics=checkpoint['text'],
                provenance=dict(provider_capabilities(settings), lyrics=checkpoint, runtime=provider_metadata),
                audio_recomposed=not reuse_audio))
            c.execute(db.links.insert().values(workspace_id=settings.workspace_id, version_id=version_id, artifact_id=artifact_id, role='audio'))
            values = {'next_version_number': project['next_version_number'] + 1}
            if project['selection_epoch'] == current['selection_epoch'] and project['latest_submission_seq'] == current['submission_seq']:
                values.update(active_version_id=version_id, revision=project['revision'] + 1)
            c.execute(db.projects.update().where(db.projects.c.id == project['id']).values(**values))
            c.execute(db.jobs.update().where(db.jobs.c.id == job['id']).values(state='succeeded', result_version_id=version_id, completed_at=timestamp))
            c.execute(db.attempts.update().where(db.attempts.c.job_id == job['id'], db.attempts.c.fence_token == fence)
                .values(ended_at=timestamp, outcome='succeeded'))
        log.info('job_succeeded job=%s correlation=%s fence=%s version=%s', job['id'], envelope.correlation_id, fence, version_id)
    except Exception as exc:
        code = exc.code if isinstance(exc, ProviderError) else 'transient_failure'
        retryable = exc.retryable if isinstance(exc, ProviderError) else True
        if isinstance(exc, OSError) and exc.errno in (28, 122):
            code, retryable = 'resource_exhaustion', False
        log.warning('job_stopped job=%s fence=%s code=%s', envelope.job_id, fence, code)
        if fence is None and code == 'incompatible_envelope': raise
        if fence is not None:
            try:
                with engine.begin() as c:
                    _, current = lock_job(c, envelope.job_id, settings)
                    if current['fence_token'] == fence and current['state'] in ('running', 'cancellation_requested'):
                        # A stale process cannot make any lifecycle decision after losing its lease.
                        attempt = c.execute(sa.select(db.attempts).where(db.attempts.c.job_id == current['id'], db.attempts.c.fence_token == fence)).mappings().one()
                        if code != 'lease_lost' and attempt['lease_expires_at'] > now(c):
                            finish_error(c, current, settings, code, retryable)
            except Exception: log.warning('job_outcome_deferred job=%s', envelope.job_id)
    finally:
        stop.set()
        if heartbeat: heartbeat.join(timeout=6)
        if temporary: temporary.unlink(missing_ok=True)
        if worker_id:
            try:
                with engine.begin() as c:
                    c.execute(db.registrations.update().where(db.registrations.c.id == worker_id).values(readiness='ready'))
            except Exception: pass
        engine.dispose()
