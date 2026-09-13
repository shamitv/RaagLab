"""One-shot schema upgrade. All callers serialize on a session advisory lock."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from museforge.config import Settings
from museforge.db.connection import engine_for

SCHEMA_HEAD = "0001_foundation"
MIGRATION_LOCK = 0x4D555345464F5247


def migrate(settings: Settings):
    engine = engine_for(settings)
    config = Config(str(Path("alembic.ini").resolve()))
    try:
        with engine.connect() as connection:
            # Session lock survives the commit required before Alembic's transaction.
            connection.execute(text("SET statement_timeout = '120s'"))
            connection.execute(text("SELECT pg_advisory_lock(:key)"), {"key": MIGRATION_LOCK})
            connection.commit()
            try:
                config.attributes["connection"] = connection
                command.upgrade(config, "head")
                with connection.begin():
                    connection.execute(text("INSERT INTO workspaces (id) VALUES (:id) ON CONFLICT (singleton) DO NOTHING"),
                                       {"id": settings.workspace_id})
                    actual = connection.scalar(text("SELECT id FROM workspaces"))
                    if actual != settings.workspace_id:
                        raise RuntimeError("configured workspace differs from persisted local workspace")
            finally:
                connection.rollback()
                connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": MIGRATION_LOCK})
                connection.commit()
    finally:
        engine.dispose()


def main():
    try:
        migrate(Settings())
    except Exception as exc:
        # URLs, credentials and SQL parameters must not enter routine logs.
        raise SystemExit(f"Migration failed ({type(exc).__name__}); check database configuration and migration compatibility") from None
    print(f"Migration complete: {SCHEMA_HEAD}")


if __name__ == "__main__":
    main()
