"""Read-only-by-default artifact inventory and reference-safe garbage collection."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
from uuid import UUID

import sqlalchemy as sa

from museforge.config import Settings
from museforge.db import schema as db
from museforge.db.connection import engine_for
from museforge.domain import ProviderError
from museforge.storage import resolve

FINAL_FILE = re.compile(
    r"^(?P<job>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})-"
    r"(?P<fence>[0-9]+)-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.wav$"
)
TEMP_FILE = re.compile(
    r"^\.(?P<job>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})-"
    r"(?P<fence>[0-9]+)-[A-Za-z0-9_-]+\.tmp$"
)


def parse_attempt_file(name):
    match = FINAL_FILE.fullmatch(name) or TEMP_FILE.fullmatch(name)
    if not match:
        return None
    return UUID(match.group("job")), int(match.group("fence"))


def has_live_attempt(connection, name, workspace_id, timestamp):
    parsed = parse_attempt_file(name)
    if not parsed:
        return False
    job_id, fence = parsed
    return bool(connection.scalar(sa.select(sa.exists().where(
        db.jobs.c.id == job_id,
        db.jobs.c.workspace_id == workspace_id,
        db.jobs.c.fence_token == fence,
        db.jobs.c.state.in_(("running", "cancellation_requested")),
        db.attempts.c.job_id == job_id,
        db.attempts.c.fence_token == fence,
        db.attempts.c.ended_at.is_(None),
        db.attempts.c.lease_expires_at > timestamp,
    ))))


def artifact_path(root: Path, storage_key: str):
    try:
        return resolve(root, storage_key)
    except ProviderError:
        return None


def inspect(engine, settings, grace_seconds=86400, timestamp=None):
    if grace_seconds < 86400:
        raise ValueError("artifact GC grace period must be at least 24 hours")
    root = settings.artifact_root
    now = timestamp or datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=grace_seconds)
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError("artifact root is unavailable or unsafe")

    with engine.connect() as connection:
        records = connection.execute(
            sa.select(
                db.artifacts,
                sa.func.count(db.links.c.version_id).label("reference_count"),
            )
            .outerjoin(db.links, db.links.c.artifact_id == db.artifacts.c.id)
            .where(db.artifacts.c.workspace_id == settings.workspace_id)
            .group_by(db.artifacts.c.id)
            .order_by(db.artifacts.c.created_at, db.artifacts.c.id)
        ).mappings().all()
        tracked_keys = {record["storage_key"] for record in records}
        tracked = []
        for record in records:
            path = artifact_path(root, record["storage_key"])
            available = False
            if path is not None:
                try:
                    available = record["byte_size"] == path.stat().st_size
                except OSError:
                    available = False
            live = has_live_attempt(connection, record["storage_key"], settings.workspace_id, now)
            referenced = record["reference_count"] > 0
            retired = record["retired_at"]
            tracked.append({
                "artifact_id": str(record["id"]),
                "storage_key": record["storage_key"],
                "available": available,
                "reference_count": record["reference_count"],
                "live_attempt": live,
                "retired_at": retired.isoformat() if retired else None,
                "state": (
                    "missing" if not available else
                    "referenced" if referenced else
                    "protected_by_live_attempt" if live else
                    "eligible" if retired and retired <= cutoff else
                    "retirement_pending"
                ),
            })

        orphans = []
        for path in root.iterdir():
            if path.name in tracked_keys or path.is_symlink() or not path.is_file():
                continue
            parsed = parse_attempt_file(path.name)
            if not parsed:
                continue
            modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            live = has_live_attempt(connection, path.name, settings.workspace_id, now)
            if modified > cutoff:
                state = "within_grace_period"
            elif live:
                state = "protected_by_live_attempt"
            else:
                state = "eligible"
            orphans.append({
                "storage_key": path.name,
                "modified_at": modified.isoformat(),
                "age_seconds": max(0, int((now - modified).total_seconds())),
                "live_attempt": live,
                "state": state,
            })
    return {
        "mode": "inspection",
        "grace_seconds": grace_seconds,
        "checked_at": now.isoformat(),
        "missing_artifacts": [item for item in tracked if item["state"] == "missing"],
        "tracked_artifacts": tracked,
        "filesystem_orphans": orphans,
        "deletions": [],
    }


def collect(engine, settings, apply=False, grace_seconds=86400, timestamp=None):
    if grace_seconds < 86400:
        raise ValueError("artifact GC grace period must be at least 24 hours")
    now = timestamp or datetime.now(timezone.utc)
    report = inspect(engine, settings, grace_seconds, now)
    if not apply:
        return report
    report["mode"] = "apply"
    deleted = []
    errors = []

    # The first apply records when an unreferenced row entered retirement. It
    # cannot be deleted until a later run observes a full grace period.
    with engine.begin() as connection:
        for item in report["tracked_artifacts"]:
            record = connection.execute(sa.select(db.artifacts).where(
                db.artifacts.c.id == UUID(item["artifact_id"]),
                db.artifacts.c.workspace_id == settings.workspace_id,
            ).with_for_update()).mappings().first()
            if record and item["state"] == "missing" and record["available_at"] is not None:
                connection.execute(db.artifacts.update().where(
                    db.artifacts.c.id == record["id"],
                ).values(available_at=None))
            elif record and item["available"] and record["available_at"] is None:
                connection.execute(db.artifacts.update().where(
                    db.artifacts.c.id == record["id"],
                ).values(available_at=now))
        unreferenced = [
            item for item in report["tracked_artifacts"]
            if item["reference_count"] == 0 and item["state"] != "missing"
        ]
        for item in unreferenced:
            record = connection.execute(sa.select(db.artifacts).where(
                db.artifacts.c.id == UUID(item["artifact_id"]),
                db.artifacts.c.workspace_id == settings.workspace_id,
            ).with_for_update()).mappings().first()
            if not record:
                continue
            count = connection.scalar(sa.select(sa.func.count()).select_from(db.links).where(
                db.links.c.artifact_id == record["id"],
            ))
            if count == 0 and record["retired_at"] is None:
                connection.execute(db.artifacts.update().where(
                    db.artifacts.c.id == record["id"],
                ).values(retired_at=now))

    report = inspect(engine, settings, grace_seconds, now)
    report["mode"] = "apply"
    cutoff = now - timedelta(seconds=grace_seconds)
    for item in report["tracked_artifacts"]:
        if item["state"] != "eligible":
            continue
        identifier = UUID(item["artifact_id"])
        path = None
        should_delete = False
        with engine.begin() as connection:
            record = connection.execute(sa.select(db.artifacts).where(
                db.artifacts.c.id == identifier,
                db.artifacts.c.workspace_id == settings.workspace_id,
            ).with_for_update()).mappings().first()
            if not record or not record["retired_at"] or record["retired_at"] > cutoff:
                continue
            references = connection.scalar(sa.select(sa.func.count()).select_from(db.links).where(
                db.links.c.artifact_id == identifier,
            ))
            if references or has_live_attempt(connection, record["storage_key"], settings.workspace_id, now):
                continue
            path = artifact_path(settings.artifact_root, record["storage_key"])
            connection.execute(db.artifacts.delete().where(db.artifacts.c.id == identifier))
            should_delete = True
        if should_delete:
            if path is not None:
                try:
                    path.unlink(missing_ok=True)
                except OSError as exc:
                    errors.append({"storage_key": item["storage_key"], "error": type(exc).__name__})
            deleted.append({"artifact_id": str(identifier), "storage_key": item["storage_key"]})

    for item in report["filesystem_orphans"]:
        if item["state"] != "eligible":
            continue
        path = settings.artifact_root / item["storage_key"]
        if path.is_symlink() or not path.is_file():
            continue
        with engine.begin() as connection:
            exists = connection.scalar(sa.select(sa.exists().where(
                db.artifacts.c.workspace_id == settings.workspace_id,
                db.artifacts.c.storage_key == item["storage_key"],
            )))
            live = has_live_attempt(connection, item["storage_key"], settings.workspace_id, now)
            if exists or live:
                continue
            try:
                path.unlink()
                deleted.append({"storage_key": item["storage_key"]})
            except OSError as exc:
                errors.append({"storage_key": item["storage_key"], "error": type(exc).__name__})

    report["deletions"] = deleted
    report["errors"] = errors
    return report


def main():
    parser = argparse.ArgumentParser(description="Inspect or safely collect retired MuseForge audio artifacts")
    parser.add_argument("--apply", action="store_true", help="delete eligible artifacts after checking references and live attempts")
    parser.add_argument("--grace-hours", type=int, default=24, help="retention grace period; minimum 24 hours (default: 24)")
    args = parser.parse_args()
    if args.grace_hours < 24:
        parser.error("--grace-hours must be at least 24")
    settings = Settings()
    engine = engine_for(settings)
    try:
        report = collect(engine, settings, apply=args.apply, grace_seconds=args.grace_hours * 3600)
        print(json.dumps(report, indent=2, sort_keys=True))
    except Exception as exc:
        parser.exit(2, f"Artifact inspection failed ({type(exc).__name__}); check database and artifact storage configuration.\n")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
