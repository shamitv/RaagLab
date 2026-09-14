"""Persist the startup-selected inference device in worker registrations."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0004_worker_runtime'
down_revision = '0003_workspace_settings'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('worker_registrations', sa.Column('runtime_metadata', JSONB(),
        nullable=False, server_default=sa.text("'{}'::jsonb")))


def downgrade():
    op.drop_column('worker_registrations', 'runtime_metadata')
