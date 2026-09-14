"""PostgreSQL authoritative acceptance and lifecycle transactions."""
import hashlib
import json
import secrets
from datetime import timedelta
from uuid import UUID, uuid4
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from museforge.db import schema as db
from museforge.domain import ProviderError, provider_capabilities

TERMINAL = {'succeeded', 'failed', 'cancelled', 'timed_out'}


def now(c): return c.scalar(sa.select(sa.func.clock_timestamp()))


def scoped(table, settings): return table.c.workspace_id == settings.workspace_id


def row(c, table, identifier, settings, lock=False):
    query = sa.select(table).where(table.c.id == identifier, scoped(table, settings))
    result = c.execute(query.with_for_update() if lock else query).mappings().first()
    if result is None: raise ProviderError('not_found')
    return dict(result)


def lock_job(c, identifier, settings):
    initial = row(c, db.jobs, identifier, settings)
    project = row(c, db.projects, initial['project_id'], settings, True)
    return project, row(c, db.jobs, identifier, settings, True)


def accepted(job):
    return dict(job_id=job['id'], project_id=job['project_id'], state=job['state'],
                status_url=f"/api/v1/jobs/{job['id']}", project_url=f"/projects/{job['project_id']}")


def insert_outbox(c, job, settings, at=None):
    c.execute(db.outbox.insert().values(id=uuid4(), workspace_id=settings.workspace_id, job_id=job['id'],
        correlation_id=job['correlation_id'], provider_route=job['provider_route'],
        dispatch_sequence=job['dispatch_sequence'], next_publication_at=at or now(c)))


def submit(engine, settings, request, key, operation="generate", source_id=None):
    if settings.music_provider == 'yue2':
        if operation != 'generate' or request.language != 'English' or request.iteration_instruction is not None:
            raise ProviderError('unsupported_capability')
        if request.lyrics.mode != 'user' or not request.lyrics.text or not request.lyrics.text.strip():
            raise ProviderError('invalid_request')
    intent = request.model_dump(mode='json')
    # Configurable defaults must not change an already accepted replay's hash.
    if 'lyrics' not in request.model_fields_set: intent['lyrics'] = None
    if 'duration_seconds' not in request.model_fields_set: intent['duration_seconds'] = None
    intent.update(operation=operation, source_version_id=str(source_id) if source_id else None)
    namespace = operation + (':' + str(source_id) if source_id else '')
    digest = hashlib.sha256(json.dumps(intent, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    def replay(c):
        record = c.execute(sa.select(db.idempotency).where(scoped(db.idempotency, settings),
            db.idempotency.c.operation_namespace == namespace, db.idempotency.c.key == key)).mappings().first()
        if record:
            if record['intent_hash'] != digest: raise ProviderError('idempotency_conflict')
            return accepted(row(c, db.jobs, record['job_id'], settings))
    try:
        with engine.begin() as c:
            existing = replay(c)
            if existing: return existing
            execution_intent = request.model_dump(mode='json')
            if intent['lyrics'] is None:
                if settings.lyrics_provider == 'user': raise ProviderError('invalid_request')
                execution_intent['lyrics'] = {'mode': settings.lyrics_provider, 'text': None}
            if intent['duration_seconds'] is None: execution_intent['duration_seconds'] = settings.duration_seconds
            source = row(c, db.versions, source_id, settings) if source_id else None
            if source:
                if request.project_id != source['project_id']: raise ProviderError('invalid_request')
                if operation == 'lyrics_edit':
                    execution_intent = {k: v for k, v in source['inputs'].items() if k in type(request).model_fields}
                    execution_intent.update(lyrics=request.lyrics.model_dump(), iteration_instruction=request.iteration_instruction)
            mode = execution_intent['lyrics']['mode']
            duration = execution_intent['duration_seconds']
            project_id = request.project_id or uuid4()
            if request.project_id is None:
                c.execute(db.projects.insert().values(id=project_id, workspace_id=settings.workspace_id,
                    title=request.brief.strip()[:120], draft=execution_intent))
            project = row(c, db.projects, project_id, settings, True)
            if project['archived_at']: raise ProviderError('project_archived')
            sequence = project['latest_submission_seq'] + 1
            c.execute(db.projects.update().where(db.projects.c.id == project_id).values(latest_submission_seq=sequence))
            limits = {name: getattr(settings, name) for name in ('heartbeat_seconds', 'lease_seconds', 'attempt_deadline_seconds',
                'hard_watchdog_seconds', 'max_attempts', 'queue_deadline_seconds', 'cancellation_grace_seconds')}
            provider_snapshot = provider_capabilities(settings)
            snapshot = dict(execution_intent, schema_version=1, workspace_id=str(settings.workspace_id), project_id=str(project_id),
                operation=operation, source_version_id=str(source_id) if source_id else None, seed=request.seed if request.seed is not None else secrets.randbits(32),
                providers={'lyrics': mode, 'music': settings.provider_id, 'provider_revision': settings.provider_revision,
                           'route': settings.provider_route, 'model_id': settings.model_id,
                           'model_revision': settings.model_revision, 'decoder_revision': settings.decoder_revision},
                capabilities=provider_snapshot,
                requested_duration_seconds=duration, effective_duration_seconds=duration,
                tempo_bounds={'Slow': [60,90], 'Medium': [100,120], 'Fast': [130,160]}[request.tempo], limits=limits,
                fixture_id='morning-spark' if mode == 'static' else None,
                fixture_revision='1' if mode == 'static' else None)
            if settings.mock_test_enabled:
                snapshot['_test'] = settings.mock_test_scenarios.get(str(snapshot['seed']), {})
            if settings.music_provider == 'yue2':
                snapshot['yue2_test_smoke'] = settings.yue2_test_smoke
            job = dict(id=uuid4(), workspace_id=settings.workspace_id, project_id=project_id, operation=operation,
                source_version_id=source_id, intent_hash=digest, execution_snapshot=snapshot,
                provider_route=settings.provider_route, state='queued',
                selection_epoch=project['selection_epoch'], submission_seq=sequence, dispatch_sequence=1,
                queue_deadline=now(c) + timedelta(seconds=settings.queue_deadline_seconds), correlation_id=uuid4())
            c.execute(db.jobs.insert().values(**job))
            response = accepted(job)
            c.execute(db.idempotency.insert().values(workspace_id=settings.workspace_id, operation_namespace=namespace,
                key=key, intent_hash=digest, job_id=job['id'], response_identity={k: str(v) for k,v in response.items()}))
            insert_outbox(c, job, settings)
            return response
    except IntegrityError:
        with engine.begin() as c:
            existing = replay(c)
            if existing: return existing
        raise


def retry(engine, settings, identifier, key):
    """Create one explicitly linked job while preserving its execution snapshot."""
    namespace = f'retry:{identifier}'

    def replay(c, digest):
        record = c.execute(sa.select(db.idempotency).where(
            scoped(db.idempotency, settings),
            db.idempotency.c.operation_namespace == namespace,
            db.idempotency.c.key == key,
        )).mappings().first()
        if record:
            if record['intent_hash'] != digest:
                raise ProviderError('idempotency_conflict')
            return accepted(row(c, db.jobs, record['job_id'], settings))
        return None

    try:
        with engine.begin() as c:
            project, original = lock_job(c, identifier, settings)
            snapshot = json.loads(json.dumps(original['execution_snapshot']))
            digest = hashlib.sha256(json.dumps(
                {'retry_of_job_id': str(identifier), 'snapshot': snapshot},
                sort_keys=True, ensure_ascii=False, separators=(',', ':')
            ).encode()).hexdigest()
            prior = replay(c, digest)
            if prior:
                return prior
            if original['state'] not in ('failed', 'timed_out'):
                raise ProviderError('retry_not_allowed')
            if original['operation'] == 'retry':
                raise ProviderError('retry_not_allowed')
            if project['archived_at']:
                raise ProviderError('project_archived')
            if snapshot.get('schema_version') != original['snapshot_schema_version']:
                raise ProviderError('retry_not_allowed')
            source_id = original['source_version_id'] or (
                UUID(snapshot['source_version_id'])
                if snapshot.get('source_version_id') else None
            )
            timestamp = now(c)
            sequence = project['latest_submission_seq'] + 1
            c.execute(db.projects.update().where(db.projects.c.id == project['id']).values(
                latest_submission_seq=sequence,
            ))
            job = dict(
                id=uuid4(),
                workspace_id=settings.workspace_id,
                project_id=original['project_id'],
                source_version_id=source_id,
                retry_of_job_id=original['id'],
                operation='retry',
                intent_hash=digest,
                execution_snapshot=snapshot,
                lyrics_checkpoint=original['lyrics_checkpoint'],
                snapshot_schema_version=original['snapshot_schema_version'],
                provider_route=original['provider_route'],
                state='queued',
                stage='awaiting_worker',
                selection_epoch=project['selection_epoch'],
                submission_seq=sequence,
                dispatch_sequence=1,
                queue_deadline=timestamp + timedelta(
                    seconds=snapshot['limits']['queue_deadline_seconds'],
                ),
                correlation_id=uuid4(),
            )
            c.execute(db.jobs.insert().values(**job))
            response = accepted(job)
            c.execute(db.idempotency.insert().values(
                workspace_id=settings.workspace_id,
                operation_namespace=namespace,
                key=key,
                intent_hash=digest,
                job_id=job['id'],
                response_identity={k: str(v) for k, v in response.items()},
            ))
            insert_outbox(c, job, settings)
            return response
    except IntegrityError:
        with engine.begin() as c:
            original = row(c, db.jobs, identifier, settings)
            snapshot = json.loads(json.dumps(original['execution_snapshot']))
            digest = hashlib.sha256(json.dumps(
                {'retry_of_job_id': str(identifier), 'snapshot': snapshot},
                sort_keys=True, ensure_ascii=False, separators=(',', ':')
            ).encode()).hexdigest()
            prior = replay(c, digest)
            if prior:
                return prior
        raise


def cancel(engine, settings, identifier):
    with engine.begin() as c:
        _, job = lock_job(c, identifier, settings)
        if job['state'] in TERMINAL: return job
        timestamp = now(c)
        state = 'cancelled' if job['state'] in ('queued', 'retrying') else 'cancellation_requested'
        values = dict(state=state, cancellation_requested_at=job['cancellation_requested_at'] or timestamp)
        if state == 'cancelled':
            values['completed_at'] = timestamp
            c.execute(db.outbox.update().where(db.outbox.c.job_id == identifier,
                db.outbox.c.state.in_(['pending', 'publishing'])).values(state='abandoned', claim_token=None, claim_expires_at=None))
        c.execute(db.jobs.update().where(db.jobs.c.id == identifier).values(**values))
        return dict(job, **values)


def owned(c, job, fence, settings):
    timestamp = now(c)
    attempt = c.execute(sa.select(db.attempts).where(db.attempts.c.job_id == job['id'],
        db.attempts.c.fence_token == fence).with_for_update()).mappings().first()
    if job['state'] == 'cancellation_requested': raise ProviderError('cancelled')
    if job['state'] != 'running' or job['fence_token'] != fence or not attempt or attempt['lease_expires_at'] <= timestamp:
        raise ProviderError('lease_lost')
    if job['attempt_deadline'] <= timestamp: raise ProviderError('deadline_exceeded')
    return timestamp


def finish_error(c, job, settings, code, retryable=False):
    timestamp = now(c)
    limits = job['execution_snapshot']['limits']
    if job['state'] in TERMINAL: return
    state = 'cancelled' if job['state'] == 'cancellation_requested' or code == 'cancelled' else 'timed_out' if code == 'deadline_exceeded' else 'failed'
    if state == 'failed' and retryable and job['attempt_count'] < limits['max_attempts'] and timestamp < job['queue_deadline']:
        state = 'retrying'
    c.execute(db.attempts.update().where(db.attempts.c.job_id == job['id'], db.attempts.c.fence_token == job['fence_token'],
        db.attempts.c.ended_at.is_(None)).values(ended_at=timestamp, outcome=state, error_code=code))
    values = dict(state=state, error_code=code, completed_at=timestamp if state in TERMINAL else None)
    if state == 'retrying':
        at = timestamp + timedelta(seconds=min(30, 2 ** job['attempt_count']) + secrets.randbelow(1000) / 1000)
        values.update(next_action_at=at, dispatch_sequence=job['dispatch_sequence'] + 1, stage='awaiting_worker')
        insert_outbox(c, dict(job, **values), settings, at)
    c.execute(db.jobs.update().where(db.jobs.c.id == job['id']).values(**values))
