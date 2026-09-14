"""Artifact collection must retain referenced media and wait out its grace period."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4
import os
import time

import httpx
import sqlalchemy as sa

from museforge.db import schema as db
from museforge.maintenance import collect
from test_generation_pipeline import BASE, submit, wait


def old_file(path: Path, content=b"orphan media"):
    path.write_bytes(content)
    old = time.time() - 25 * 60 * 60
    os.utime(path, (old, old))


def test_gc_is_inspection_first_and_protects_references_and_live_attempts(engine, settings):
    accepted, _ = submit(seed=77)
    completed, _ = wait(accepted)
    version = httpx.get(BASE + completed["version_url"]).json()
    duplicate = httpx.post(BASE + f"/api/v1/projects/{version['project_id']}/duplicate")
    assert duplicate.status_code == 201, duplicate.text
    artifact_id = UUID(version["audio"]["id"])
    with engine.connect() as connection:
        key = connection.scalar(sa.select(db.artifacts.c.storage_key).where(db.artifacts.c.id == artifact_id))
        references = connection.scalar(sa.select(sa.func.count()).select_from(db.links).where(db.links.c.artifact_id == artifact_id))
    assert references == 2
    referenced_file = settings.artifact_root / key
    dry = collect(engine, settings)
    item = next(record for record in dry["tracked_artifacts"] if record["artifact_id"] == str(artifact_id))
    assert item["state"] == "referenced"
    assert dry["deletions"] == []
    applied = collect(engine, settings, apply=True)
    assert not any(record.get("artifact_id") == str(artifact_id) for record in applied["deletions"])
    assert referenced_file.is_file()

    now = datetime.now(timezone.utc)
    retired_id = uuid4()
    retired_name = f"{uuid4()}-3-{uuid4()}.wav"
    retired_path = settings.artifact_root / retired_name
    old_file(retired_path)
    content = retired_path.read_bytes()
    with engine.begin() as connection:
        connection.execute(db.artifacts.insert().values(
            id=retired_id,
            workspace_id=settings.workspace_id,
            created_at=now - timedelta(hours=26),
            storage_key=retired_name,
            sha256="a" * 64,
            byte_size=len(content),
            media_type="audio/wav",
            sample_rate=44100,
            channels=2,
            duration_seconds=5,
            published_at=now - timedelta(hours=25),
            available_at=now - timedelta(hours=25),
            retired_at=now - timedelta(hours=25),
        ))
    retired_dry = collect(engine, settings)
    retired_item = next(record for record in retired_dry["tracked_artifacts"] if record["artifact_id"] == str(retired_id))
    assert retired_item["state"] == "eligible"
    assert retired_path.is_file()
    retired_apply = collect(engine, settings, apply=True)
    assert any(record.get("artifact_id") == str(retired_id) for record in retired_apply["deletions"])
    assert not retired_path.exists()
    with engine.connect() as connection:
        assert connection.scalar(sa.select(sa.func.count()).select_from(db.artifacts).where(db.artifacts.c.id == retired_id)) == 0

    pending_id = uuid4()
    pending_name = f"{uuid4()}-2-{uuid4()}.wav"
    pending_path = settings.artifact_root / pending_name
    pending_path.write_bytes(b"recent unreferenced artifact")
    pending_bytes = pending_path.read_bytes()
    with engine.begin() as connection:
        connection.execute(db.artifacts.insert().values(
            id=pending_id,
            workspace_id=settings.workspace_id,
            storage_key=pending_name,
            sha256="c" * 64,
            byte_size=len(pending_bytes),
            media_type="audio/wav",
            sample_rate=44100,
            channels=2,
            duration_seconds=5,
            published_at=now,
            available_at=now,
        ))
    inspection = collect(engine, settings)
    pending_item = next(record for record in inspection["tracked_artifacts"] if record["artifact_id"] == str(pending_id))
    assert pending_item["state"] == "retirement_pending"
    first_apply = collect(engine, settings, apply=True)
    assert not any(record.get("artifact_id") == str(pending_id) for record in first_apply["deletions"])
    assert pending_path.is_file()
    with engine.connect() as connection:
        retired_at = connection.scalar(sa.select(db.artifacts.c.retired_at).where(db.artifacts.c.id == pending_id))
    assert retired_at is not None
    matured = collect(engine, settings, apply=True, timestamp=retired_at + timedelta(hours=25))
    assert any(record.get("artifact_id") == str(pending_id) for record in matured["deletions"])
    assert not pending_path.exists()

    job_id, worker_id, project_id = uuid4(), uuid4(), uuid4()
    correlation_id = uuid4()
    live_name = f"{job_id}-7-{uuid4()}.wav"
    live_path = settings.artifact_root / live_name
    old_file(live_path)
    live_until = datetime.now(timezone.utc) + timedelta(minutes=2)
    limits = {
        "heartbeat_seconds": settings.heartbeat_seconds,
        "lease_seconds": settings.lease_seconds,
        "attempt_deadline_seconds": settings.attempt_deadline_seconds,
        "hard_watchdog_seconds": settings.hard_watchdog_seconds,
        "max_attempts": settings.max_attempts,
        "queue_deadline_seconds": settings.queue_deadline_seconds,
        "cancellation_grace_seconds": settings.cancellation_grace_seconds,
    }
    try:
        with engine.begin() as connection:
            connection.execute(db.projects.insert().values(
                id=project_id, workspace_id=settings.workspace_id, title="GC live attempt fixture",
            ))
            connection.execute(db.jobs.insert().values(
                id=job_id,
                workspace_id=settings.workspace_id,
                project_id=project_id,
                operation="generate",
                intent_hash="b" * 64,
                execution_snapshot={"schema_version": 1, "limits": limits},
                provider_route=settings.mock_queue,
                state="running",
                attempt_count=1,
                fence_token=7,
                selection_epoch=0,
                submission_seq=1,
                queue_deadline=live_until,
                attempt_deadline=live_until,
                correlation_id=correlation_id,
            ))
            # Keep the durable fixture API-readable during subsequent restart
            # sweeps; every application job has a matching dispatch record.
            connection.execute(db.outbox.insert().values(
                workspace_id=settings.workspace_id, job_id=job_id,
                correlation_id=correlation_id, provider_route=settings.mock_queue,
                dispatch_sequence=1, state="published", confirmed_at=now,
            ))
            connection.execute(db.registrations.insert().values(
                id=worker_id,
                workspace_id=settings.workspace_id,
                worker_name=f"gc-fixture-{worker_id}",
                provider_id="mock",
                provider_revision="1",
                provider_route=settings.mock_queue,
                capability_revision="1",
                readiness="busy",
                last_heartbeat=now,
                expires_at=live_until,
            ))
            connection.execute(db.attempts.insert().values(
                workspace_id=settings.workspace_id,
                job_id=job_id,
                worker_id=worker_id,
                attempt_number=1,
                fence_token=7,
                heartbeat_at=now,
                lease_expires_at=live_until,
            ))
        live_dry = collect(engine, settings)
        live_item = next(record for record in live_dry["filesystem_orphans"] if record["storage_key"] == live_name)
        assert live_item["state"] == "protected_by_live_attempt"
        live_apply = collect(engine, settings, apply=True)
        assert not any(record.get("storage_key") == live_name for record in live_apply["deletions"])
        assert live_path.is_file()
    finally:
        live_path.unlink(missing_ok=True)
        with engine.begin() as connection:
            timestamp = connection.scalar(sa.select(sa.func.now()))
            connection.execute(db.jobs.update().where(db.jobs.c.id == job_id).values(state="failed", completed_at=timestamp, error_code="test_fixture"))
            connection.execute(db.attempts.update().where(db.attempts.c.job_id == job_id).values(ended_at=timestamp, outcome="failed"))
