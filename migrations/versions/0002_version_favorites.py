"""Version favorite relation for the responsive workspace."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
revision = '0002_version_favorites'
down_revision = '0001_foundation'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('version_favorites',
        sa.Column('workspace_id', UUID(as_uuid=True), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('version_id', UUID(as_uuid=True), primary_key=True),
        sa.ForeignKeyConstraint(['workspace_id', 'version_id'], ['song_versions.workspace_id', 'song_versions.id']))


def downgrade():
    op.drop_table('version_favorites')
