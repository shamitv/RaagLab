"""Relational foundation; flexible snapshots are versioned JSONB objects."""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

metadata = sa.MetaData(naming_convention={
    "ix": "ix_%(table_name)s_%(column_0_name)s", "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s", "ck": "ck_%(table_name)s_%(constraint_name)s",
})


def identity():
    return sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))


def created():
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def workspace():
    return sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False)


def json_column(name, nullable=False):
    return sa.Column(name, JSONB, nullable=nullable, server_default=None if nullable else sa.text("'{}'::jsonb"))


workspaces = sa.Table("workspaces", metadata, identity(), created(),
    sa.Column("singleton", sa.Boolean, nullable=False, server_default=sa.true(), unique=True),
    sa.CheckConstraint("singleton", name="local_singleton"),
)
projects = sa.Table("projects", metadata, identity(), workspace(), created(),
    sa.Column("title", sa.String(120), nullable=False), json_column("draft"),
    sa.Column("revision", sa.BigInteger, nullable=False, server_default="1"),
    sa.Column("active_version_id", UUID(as_uuid=True)),
    sa.Column("selection_epoch", sa.BigInteger, nullable=False, server_default="0"),
    sa.Column("latest_submission_seq", sa.BigInteger, nullable=False, server_default="0"),
    sa.Column("next_version_number", sa.BigInteger, nullable=False, server_default="1"),
    sa.Column("archived_at", sa.DateTime(timezone=True)),
    sa.UniqueConstraint("workspace_id", "id", name="uq_projects_workspace_id_id"),
    sa.CheckConstraint("length(btrim(title)) > 0", name="nonblank_title"),
    sa.CheckConstraint("revision > 0 AND selection_epoch >= 0 AND latest_submission_seq >= 0 AND next_version_number > 0", name="counters"),
    sa.CheckConstraint("jsonb_typeof(draft) = 'object'", name="draft_object"),
)
jobs = sa.Table("generation_jobs", metadata, identity(), workspace(), created(),
    sa.Column("project_id", UUID(as_uuid=True), nullable=False),
    sa.Column("source_version_id", UUID(as_uuid=True)),
    sa.Column("retry_of_job_id", UUID(as_uuid=True)),
    sa.Column("result_version_id", UUID(as_uuid=True)),
    sa.Column("operation", sa.String(32), nullable=False),
    sa.Column("intent_hash", sa.String(64), nullable=False),
    json_column("execution_snapshot"), json_column("lyrics_checkpoint", nullable=True),
    sa.Column("snapshot_schema_version", sa.Integer, nullable=False, server_default="1"),
    sa.Column("provider_route", sa.String(128), nullable=False),
    sa.Column("state", sa.String(32), nullable=False, server_default="queued"),
    sa.Column("stage", sa.String(32), nullable=False, server_default="awaiting_worker"),
    sa.Column("progress", sa.Float),
    sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
    sa.Column("fence_token", sa.BigInteger, nullable=False, server_default="0"),
    sa.Column("dispatch_sequence", sa.BigInteger, nullable=False, server_default="1"),
    sa.Column("selection_epoch", sa.BigInteger, nullable=False),
    sa.Column("submission_seq", sa.BigInteger, nullable=False),
    sa.Column("queue_deadline", sa.DateTime(timezone=True), nullable=False),
    sa.Column("attempt_deadline", sa.DateTime(timezone=True)),
    sa.Column("next_action_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.Column("cancellation_requested_at", sa.DateTime(timezone=True)),
    sa.Column("completed_at", sa.DateTime(timezone=True)),
    sa.Column("error_code", sa.String(80)),
    sa.Column("correlation_id", UUID(as_uuid=True), nullable=False),
    sa.UniqueConstraint("workspace_id", "project_id", "id", name="uq_jobs_scope_id"),
    sa.UniqueConstraint("workspace_id", "id", name="uq_jobs_workspace_id_id"),
    sa.ForeignKeyConstraint(["workspace_id", "project_id"], ["projects.workspace_id", "projects.id"]),
    sa.ForeignKeyConstraint(["workspace_id", "project_id", "retry_of_job_id"], ["generation_jobs.workspace_id", "generation_jobs.project_id", "generation_jobs.id"], name="fk_jobs_retry_scope"),
    sa.CheckConstraint("state IN ('queued','running','retrying','cancellation_requested','cancelled','succeeded','failed','timed_out')", name="state"),
    sa.CheckConstraint("stage IN ('awaiting_worker','writing_lyrics','composing_music','validating_audio','saving_result')", name="stage"),
    sa.CheckConstraint("operation IN ('generate','refine','variation','regenerate','lyrics_edit','retry')", name="operation"),
    sa.CheckConstraint("progress IS NULL OR (progress >= 0 AND progress <= 1)", name="progress"),
    sa.CheckConstraint("attempt_count >= 0 AND fence_token >= 0 AND dispatch_sequence > 0 AND submission_seq > 0 AND selection_epoch >= 0", name="counters"),
    sa.CheckConstraint("intent_hash ~ '^[0-9a-f]{64}$'", name="intent_hash"),
    sa.CheckConstraint("snapshot_schema_version > 0 AND jsonb_typeof(execution_snapshot) = 'object'", name="snapshot"),
)
versions = sa.Table("song_versions", metadata, identity(), workspace(), created(),
    sa.Column("project_id", UUID(as_uuid=True), nullable=False),
    sa.Column("parent_version_id", UUID(as_uuid=True)),
    sa.Column("origin_version_id", UUID(as_uuid=True)),
    sa.Column("generation_job_id", UUID(as_uuid=True), unique=True),
    sa.Column("number", sa.BigInteger, nullable=False),
    sa.Column("label", sa.String(120), nullable=False),
    sa.Column("revision", sa.BigInteger, nullable=False, server_default="1"),
    json_column("inputs"), sa.Column("lyrics", sa.Text, nullable=False),
    json_column("structure", nullable=True), json_column("provenance"),
    sa.Column("snapshot_schema_version", sa.Integer, nullable=False, server_default="1"),
    sa.Column("audio_recomposed", sa.Boolean, nullable=False),
    sa.UniqueConstraint("project_id", "number", name="uq_versions_project_number"),
    sa.UniqueConstraint("workspace_id", "project_id", "id", name="uq_versions_scope_id"),
    sa.UniqueConstraint("workspace_id", "id", name="uq_versions_workspace_id_id"),
    sa.ForeignKeyConstraint(["workspace_id", "project_id"], ["projects.workspace_id", "projects.id"]),
    sa.ForeignKeyConstraint(["workspace_id", "project_id", "parent_version_id"], ["song_versions.workspace_id", "song_versions.project_id", "song_versions.id"], name="fk_versions_parent_scope"),
    sa.ForeignKeyConstraint(["workspace_id", "origin_version_id"], ["song_versions.workspace_id", "song_versions.id"], name="fk_versions_origin_scope"),
    sa.ForeignKeyConstraint(["workspace_id", "project_id", "generation_job_id"], ["generation_jobs.workspace_id", "generation_jobs.project_id", "generation_jobs.id"], name="fk_versions_generation_scope"),
    sa.CheckConstraint("number > 0 AND revision > 0 AND snapshot_schema_version > 0", name="counters"),
    sa.CheckConstraint("length(btrim(label)) > 0", name="nonblank_label"),
    sa.CheckConstraint("parent_version_id IS NULL OR parent_version_id != id", name="not_own_parent"),
)
projects.append_constraint(sa.ForeignKeyConstraint(
    ["workspace_id", "id", "active_version_id"], ["song_versions.workspace_id", "song_versions.project_id", "song_versions.id"],
    name="fk_projects_active_version_scope", use_alter=True))
for column in ("source_version_id", "result_version_id"):
    jobs.append_constraint(sa.ForeignKeyConstraint(
        ["workspace_id", "project_id", column], ["song_versions.workspace_id", "song_versions.project_id", "song_versions.id"],
        name=f"fk_jobs_{column}_scope", use_alter=True))
registrations = sa.Table("worker_registrations", metadata, identity(), workspace(), created(),
    sa.Column("worker_name", sa.String(200), nullable=False, unique=True),
    sa.Column("provider_id", sa.String(128), nullable=False),
    sa.Column("provider_revision", sa.String(80), nullable=False),
    sa.Column("model_id", sa.Text), sa.Column("model_revision", sa.Text),
    sa.Column("provider_route", sa.String(128), nullable=False),
    sa.Column("capability_revision", sa.String(80), nullable=False),
    sa.Column("readiness", sa.String(32), nullable=False),
    sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.UniqueConstraint("workspace_id", "id", name="uq_workers_workspace_id_id"),
    sa.CheckConstraint("readiness IN ('initializing','ready','busy','offline')", name="readiness"),
    sa.CheckConstraint("expires_at > last_heartbeat", name="freshness"),
)
attempts = sa.Table("job_attempts", metadata, identity(), workspace(), created(),
    sa.Column("job_id", UUID(as_uuid=True), nullable=False),
    sa.Column("worker_id", UUID(as_uuid=True), nullable=False),
    sa.Column("attempt_number", sa.Integer, nullable=False),
    sa.Column("fence_token", sa.BigInteger, nullable=False),
    sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.Column("ended_at", sa.DateTime(timezone=True)),
    sa.Column("outcome", sa.String(32)), sa.Column("error_code", sa.String(80)),
    sa.UniqueConstraint("job_id", "attempt_number", name="uq_attempts_job_number"),
    sa.UniqueConstraint("job_id", "fence_token", name="uq_attempts_job_fence"),
    sa.ForeignKeyConstraint(["workspace_id", "job_id"], ["generation_jobs.workspace_id", "generation_jobs.id"]),
    sa.ForeignKeyConstraint(["workspace_id", "worker_id"], ["worker_registrations.workspace_id", "worker_registrations.id"]),
    sa.CheckConstraint("attempt_number > 0 AND fence_token > 0", name="counters"),
)
idempotency = sa.Table("idempotency_records", metadata, identity(), workspace(), created(),
    sa.Column("operation_namespace", sa.String(80), nullable=False),
    sa.Column("key", sa.String(128), nullable=False),
    sa.Column("intent_hash", sa.String(64), nullable=False),
    sa.Column("job_id", UUID(as_uuid=True), nullable=False), json_column("response_identity"),
    sa.UniqueConstraint("workspace_id", "operation_namespace", "key", name="uq_idempotency_scope_key"),
    sa.ForeignKeyConstraint(["workspace_id", "job_id"], ["generation_jobs.workspace_id", "generation_jobs.id"]),
    sa.CheckConstraint("length(key) BETWEEN 16 AND 128", name="key_length"),
    sa.CheckConstraint("intent_hash ~ '^[0-9a-f]{64}$'", name="intent_hash"),
)
outbox = sa.Table("outbox_messages", metadata, identity(), workspace(), created(),
    sa.Column("job_id", UUID(as_uuid=True), nullable=False),
    sa.Column("schema_version", sa.Integer, nullable=False, server_default="1"),
    sa.Column("correlation_id", UUID(as_uuid=True), nullable=False),
    sa.Column("provider_route", sa.String(128), nullable=False),
    sa.Column("dispatch_sequence", sa.BigInteger, nullable=False),
    sa.Column("state", sa.String(20), nullable=False, server_default="pending"),
    sa.Column("claim_token", UUID(as_uuid=True)),
    sa.Column("claim_expires_at", sa.DateTime(timezone=True)),
    sa.Column("publication_count", sa.Integer, nullable=False, server_default="0"),
    sa.Column("next_publication_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.Column("confirmed_at", sa.DateTime(timezone=True)),
    sa.Column("error_at", sa.DateTime(timezone=True)), sa.Column("error_code", sa.String(80)),
    sa.UniqueConstraint("job_id", "dispatch_sequence", name="uq_outbox_job_sequence"),
    sa.ForeignKeyConstraint(["workspace_id", "job_id"], ["generation_jobs.workspace_id", "generation_jobs.id"]),
    sa.CheckConstraint("state IN ('pending','publishing','published','abandoned')", name="state"),
    sa.CheckConstraint("schema_version > 0 AND dispatch_sequence > 0 AND publication_count >= 0", name="counters"),
    sa.CheckConstraint("state != 'publishing' OR (claim_token IS NOT NULL AND claim_expires_at IS NOT NULL)", name="publishing_claim"),
)
artifacts = sa.Table("artifacts", metadata, identity(), workspace(), created(),
    sa.Column("storage_key", sa.String(512), nullable=False, unique=True),
    sa.Column("sha256", sa.String(64), nullable=False),
    sa.Column("byte_size", sa.BigInteger, nullable=False),
    sa.Column("media_type", sa.String(120), nullable=False),
    sa.Column("sample_rate", sa.Integer, nullable=False),
    sa.Column("channels", sa.Integer, nullable=False),
    sa.Column("duration_seconds", sa.Float, nullable=False),
    sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("available_at", sa.DateTime(timezone=True)),
    sa.Column("retired_at", sa.DateTime(timezone=True)),
    sa.UniqueConstraint("workspace_id", "id", name="uq_artifacts_workspace_id_id"),
    sa.CheckConstraint("byte_size > 0 AND sample_rate > 0 AND channels > 0 AND duration_seconds > 0", name="measured_media"),
    sa.CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="checksum"),
)
links = sa.Table("version_artifacts", metadata, workspace(),
    sa.Column("version_id", UUID(as_uuid=True), primary_key=True),
    sa.Column("artifact_id", UUID(as_uuid=True), nullable=False),
    sa.Column("role", sa.String(40), primary_key=True), created(),
    sa.ForeignKeyConstraint(["workspace_id", "version_id"], ["song_versions.workspace_id", "song_versions.id"]),
    sa.ForeignKeyConstraint(["workspace_id", "artifact_id"], ["artifacts.workspace_id", "artifacts.id"]),
)
sa.Index("ix_projects_workspace_archive_created", projects.c.workspace_id, projects.c.archived_at, projects.c.created_at, projects.c.id)
sa.Index("ix_jobs_due", jobs.c.state, jobs.c.next_action_at)
sa.Index("ix_jobs_queue_deadline", jobs.c.state, jobs.c.queue_deadline)
sa.Index("ix_jobs_attempt_deadline", jobs.c.state, jobs.c.attempt_deadline)
sa.Index("ix_jobs_project_created", jobs.c.project_id, jobs.c.created_at, jobs.c.id)
sa.Index("ix_outbox_due", outbox.c.state, outbox.c.next_publication_at)
sa.Index("ix_outbox_claim_expiry", outbox.c.state, outbox.c.claim_expires_at)
sa.Index("ix_attempts_lease", attempts.c.lease_expires_at)
sa.Index("ix_workers_route_expiry", registrations.c.provider_route, registrations.c.expires_at)
sa.Index("ix_artifact_references", links.c.artifact_id)
# Operational process observations are separate from provider capability readiness.
process_heartbeats = sa.Table("process_heartbeats", metadata,
    sa.Column("role", sa.String(32), primary_key=True),
    sa.Column("instance_id", sa.String(200), primary_key=True),
    sa.Column("broker_connected", sa.Boolean, nullable=False),
    sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("role IN ('dispatcher','worker-mock')", name="role"),
    sa.CheckConstraint("expires_at > last_heartbeat", name="freshness"),
)
