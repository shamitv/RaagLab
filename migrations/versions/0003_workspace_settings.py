"""Versioned local workspace preferences."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0003_workspace_settings"
down_revision = "0002_version_favorites"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "workspace_settings",
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), primary_key=True),
        sa.Column("revision", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("generation_defaults", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("volume", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("repeat_mode", sa.String(8), nullable=False, server_default="off"),
        sa.Column("export_format", sa.String(8), nullable=False, server_default="wav"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("revision > 0", name="ck_workspace_settings_revision_positive"),
        sa.CheckConstraint("volume >= 0 AND volume <= 1", name="ck_workspace_settings_volume_range"),
        sa.CheckConstraint("repeat_mode IN ('off','one','all')", name="ck_workspace_settings_repeat_mode"),
        sa.CheckConstraint("export_format = 'wav'", name="ck_workspace_settings_export_format"),
        sa.CheckConstraint("jsonb_typeof(generation_defaults) = 'object'", name="ck_workspace_settings_defaults_object"),
    )
    op.create_index("ix_versions_library_created", "song_versions", ["workspace_id", "created_at", "id"])


def downgrade():
    op.drop_index("ix_versions_library_created", table_name="song_versions")
    op.drop_table("workspace_settings")
