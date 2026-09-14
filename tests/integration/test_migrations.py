import subprocess
import sys
import time
from uuid import uuid4
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from alembic import command
from alembic.config import Config

from museforge.db.migrate import MIGRATION_LOCK, SCHEMA_HEAD, migrate
from museforge.db.schema import metadata, projects, versions, workspaces


def test_head_and_runtime_schema(engine, settings):
    with engine.connect() as connection:
        assert int(connection.scalar(sa.text('SHOW server_version_num'))) // 10000 == 18
        assert connection.scalar(sa.text('SELECT version_num FROM alembic_version')) == SCHEMA_HEAD
        assert connection.scalar(sa.text('SELECT id FROM workspaces')) == settings.workspace_id
        assert set(metadata.tables).issubset(sa.inspect(connection).get_table_names())
        assert {'ix_jobs_due', 'ix_jobs_queue_deadline'}.issubset({i['name'] for i in sa.inspect(connection).get_indexes('generation_jobs')})


def test_rerun_and_concurrent_migrations(engine, settings):
    migrate(settings)
    # Holding the same session lock must block both independent migration processes.
    with engine.connect() as connection:
        connection.execute(sa.text('SELECT pg_advisory_lock(:key)'), {'key': MIGRATION_LOCK})
        connection.commit()
        processes = [subprocess.Popen([sys.executable, '-m', 'museforge.db.migrate'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        try:
            time.sleep(1)
            assert all(process.poll() is None for process in processes)
        finally:
            connection.execute(sa.text('SELECT pg_advisory_unlock(:key)'), {'key': MIGRATION_LOCK})
            connection.commit()
        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            assert process.returncode == 0, (stdout, stderr)
    with engine.connect() as connection:
        assert connection.scalar(sa.text('SELECT count(*) FROM workspaces')) == 1


def test_forward_upgrade_from_current_pre_phase4_head(engine, settings):
    schema = 'phase4_upgrade_' + uuid4().hex
    with engine.begin() as connection:
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql(f'SET search_path TO "{schema}"')
            connection.commit()
            config = Config(str(Path(__file__).resolve().parents[2] / 'alembic.ini'))
            config.attributes['connection'] = connection
            command.upgrade(config, '0002_version_favorites')
            assert connection.scalar(sa.text('SELECT version_num FROM alembic_version')) == '0002_version_favorites'
            connection.commit()
            assert 'workspace_settings' not in sa.inspect(connection).get_table_names()
            connection.commit()
            command.upgrade(config, '0003_workspace_settings')
            connection.commit()
            tables = set(sa.inspect(connection).get_table_names())
            assert 'workspace_settings' in tables
            assert 'version_favorites' in tables
            assert 'ix_versions_library_created' in {
                index['name'] for index in sa.inspect(connection).get_indexes('song_versions')
            }
            assert connection.scalar(sa.text('SELECT version_num FROM alembic_version')) == SCHEMA_HEAD
            connection.commit()
    finally:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')


def test_singleton_and_project_constraints(engine, settings):
    with engine.connect() as connection, connection.begin():
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(workspaces.insert().values(id=uuid4()))
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(projects.insert().values(workspace_id=settings.workspace_id, title=' '))
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(projects.insert().values(workspace_id=uuid4(), title='Wrong workspace'))


def test_version_numbers_and_parent_active_scope(engine, settings):
    # Roll back all fixture data; do not contaminate restart assertions.
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            first, second = uuid4(), uuid4()
            for project in (first, second):
                connection.execute(projects.insert().values(id=project, workspace_id=settings.workspace_id, title='Foundation test'))
            version = uuid4()
            values = dict(id=version, workspace_id=settings.workspace_id, project_id=first, number=1,
                          label='First', lyrics='Original test', audio_recomposed=False)
            connection.execute(versions.insert().values(**values))
            connection.execute(projects.update().where(projects.c.id == first).values(active_version_id=version))
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(projects.update().where(projects.c.id == second).values(active_version_id=version))
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(versions.insert().values(**(values | {'id': uuid4()})))
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(versions.insert().values(**(values | {'id': uuid4(), 'project_id': second, 'parent_version_id': version})))
        finally:
            transaction.rollback()


def test_operational_uniqueness_and_artifact_references(engine, settings):
    from datetime import datetime, timedelta, timezone
    from museforge.db.schema import jobs, idempotency, attempts, registrations, artifacts, links, outbox
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            now = datetime.now(timezone.utc)
            project, job, worker, version, artifact = (uuid4() for _ in range(5))
            scope = {'workspace_id': settings.workspace_id}
            connection.execute(projects.insert().values(**scope, id=project, title='Constraint fixture'))
            connection.execute(jobs.insert().values(**scope, id=job, project_id=project, operation='generate',
                intent_hash='a' * 64, provider_route='museforge.mock.v1', selection_epoch=0, submission_seq=1,
                queue_deadline=now + timedelta(minutes=15), correlation_id=uuid4()))
            record = dict(**scope, job_id=job, operation_namespace='generate', key='foundation-key-01', intent_hash='a' * 64)
            connection.execute(idempotency.insert().values(**record))
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(idempotency.insert().values(**record))
            connection.execute(registrations.insert().values(**scope, id=worker, worker_name=str(worker), provider_id='mock',
                provider_revision='test', provider_route='museforge.mock.v1', capability_revision='test', readiness='initializing',
                last_heartbeat=now, expires_at=now + timedelta(seconds=30)))
            attempt = dict(**scope, job_id=job, worker_id=worker, attempt_number=1, fence_token=1,
                           heartbeat_at=now, lease_expires_at=now + timedelta(seconds=30))
            connection.execute(attempts.insert().values(**attempt))
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(attempts.insert().values(**attempt))
            message = dict(**scope, job_id=job, correlation_id=uuid4(), provider_route='museforge.mock.v1', dispatch_sequence=1)
            connection.execute(outbox.insert().values(**message))
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(outbox.insert().values(**message))
            version_values = dict(**scope, id=version, project_id=project, generation_job_id=job, number=1,
                                  label='Version', lyrics='', audio_recomposed=True)
            connection.execute(versions.insert().values(**version_values))
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(versions.insert().values(**(version_values | {'id': uuid4(), 'number': 2})))
            connection.execute(artifacts.insert().values(**scope, id=artifact, storage_key=f'test/{artifact}.wav',
                sha256='a' * 64, byte_size=100, media_type='audio/wav', sample_rate=44100, channels=2,
                duration_seconds=8, published_at=now))
            connection.execute(links.insert().values(**scope, version_id=version, artifact_id=artifact, role='audio'))
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(artifacts.delete().where(artifacts.c.id == artifact))
        finally:
            transaction.rollback()
