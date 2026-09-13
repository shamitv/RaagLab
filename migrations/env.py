from alembic import context
from museforge.db.schema import metadata

connection = context.config.attributes.get("connection")
if connection is None:
    raise RuntimeError("Use python -m museforge.db.migrate (advisory-lock guarded), not bare alembic")
context.configure(connection=connection, target_metadata=metadata, compare_type=True)
with context.begin_transaction():
    context.run_migrations()
