"""Bounded process probes; provider capability readiness remains separate."""
import json
import logging
import os
import threading
import time
from pathlib import Path

from sqlalchemy import text

from museforge.config import Settings
from museforge.db.connection import engine_for
from museforge.db.migrate import SCHEMA_HEAD

logger = logging.getLogger("museforge")


def check_schema(connection, settings):
    heads = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
    if heads != [SCHEMA_HEAD]:
        raise RuntimeError("migration_required")
    if connection.scalar(text("SELECT id FROM workspaces WHERE id = :id"), {"id": settings.workspace_id}) is None:
        raise RuntimeError("workspace_missing")


def write_probe(path: Path, *, healthy: bool, role: str):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"healthy": healthy, "role": role, "pid": os.getpid(), "observed_at": time.time()}))
    temporary.replace(path)


def probe_loop(settings: Settings, role: str, instance: str, stop: threading.Event, broker_check):
    engine = engine_for(settings)
    try:
        while not stop.is_set():
            healthy = False
            try:
                broker_check()
                with engine.begin() as connection:
                    check_schema(connection, settings)
                    connection.execute(text("""
                        INSERT INTO process_heartbeats(role, instance_id, broker_connected, last_heartbeat, expires_at)
                        VALUES (:role, :instance, true, now(), now() + :lease * interval '1 second')
                        ON CONFLICT (role, instance_id) DO UPDATE SET
                        broker_connected = true, last_heartbeat = now(), expires_at = EXCLUDED.expires_at
                    """), {"role": role, "instance": instance, "lease": settings.lease_seconds})
                    if role == "worker-mock":
                        connection.execute(text("""
                            INSERT INTO worker_registrations (workspace_id, worker_name, provider_id, provider_revision,
                              provider_route, capability_revision, readiness, last_heartbeat, expires_at)
                            VALUES (:workspace, :instance, 'mock', 'foundation', :route,
                              'foundation-no-generation', 'initializing', now(), now() + :lease * interval '1 second')
                            ON CONFLICT (worker_name) DO UPDATE SET last_heartbeat = now(),
                              expires_at = EXCLUDED.expires_at, readiness = 'initializing'
                        """), {"workspace": settings.workspace_id, "instance": instance,
                               "route": settings.mock_queue, "lease": settings.lease_seconds})
                healthy = True
            except Exception as exc:
                logger.warning("process_probe_failed role=%s error_type=%s", role, type(exc).__name__)
            write_probe(settings.health_file, healthy=healthy, role=role)
            stop.wait(settings.heartbeat_seconds)
    finally:
        write_probe(settings.health_file, healthy=False, role=role)
        engine.dispose()
