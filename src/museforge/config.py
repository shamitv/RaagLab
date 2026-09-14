from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    database_url: SecretStr = SecretStr("postgresql+psycopg://museforge:local-development-only@db:5432/museforge")
    broker_url: SecretStr = SecretStr("amqp://museforge:local-development-only@broker:5672//")
    workspace_id: UUID = UUID("00000000-0000-4000-8000-000000000001")
    artifact_root: Path = Path("/var/lib/museforge/artifacts")
    web_dist: Path = Path("/app/web")
    app_port: int = Field(8000, ge=1024, le=65535)
    app_bind: Literal["127.0.0.1"] = "127.0.0.1"
    lyrics_provider: Literal["user", "static", "mock"] = "mock"
    music_provider: Literal["mock", "yue2"] = "mock"
    mock_queue: Literal["museforge.mock.v1"] = "museforge.mock.v1"
    yue2_queue: Literal["museforge.yue2.v1"] = "museforge.yue2.v1"
    quarantine_queue: Literal["museforge.quarantine.v1"] = "museforge.quarantine.v1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    model_id: str | None = None
    model_revision: str | None = None
    decoder_revision: str | None = None
    weights_dir: Path = Path("/var/lib/museforge/weights")
    cache_dir: Path = Path("/var/cache/museforge")
    device: Literal["cpu", "cuda", "mps"] = "cpu"
    precision: Literal["float32", "float16", "bfloat16"] = "float32"
    yue2_model_dir: Path = Path("/weights/model")
    yue2_vae_dir: Path = Path("/weights/vae")
    yue2_runner: Path = Path("/opt/yue2-test/generate.py")
    yue2_preflight: Path = Path("/opt/yue2-test/preflight.py")
    yue2_process_timeout_seconds: int = Field(900, gt=0)
    yue2_warmup_timeout_seconds: int = Field(900, gt=0)
    yue2_memory_budget_gib: int = Field(16, gt=0)
    yue2_offload_ar: bool = False
    worker_concurrency: int = Field(1, ge=1, le=1)
    duration_seconds: int = Field(8, ge=5, le=30)
    dispatcher_poll_seconds: float = Field(1, gt=0)
    reconciliation_seconds: float = Field(5, gt=0)
    outbox_claim_seconds: int = Field(15, gt=0)
    broker_timeout_seconds: int = Field(5, ge=1, le=10)
    unclaimed_seconds: int = Field(60, gt=0)
    queue_deadline_seconds: int = Field(900, gt=0)
    heartbeat_seconds: float = Field(5, gt=0)
    lease_seconds: int = Field(30, gt=0)
    attempt_deadline_seconds: int = Field(60, gt=0)
    hard_watchdog_seconds: int = Field(75, gt=0)
    cancellation_grace_seconds: int = Field(10, gt=0)
    max_attempts: int = Field(3, ge=1, le=3)
    mock_test_enabled: bool = False
    mock_test_scenarios: dict[str, dict] = Field(default_factory=dict)
    mock_test_delay_seconds: float = Field(0, ge=0, le=120)
    mock_test_outcome: Literal['success', 'transient_failure', 'invalid_request', 'deadline_exceeded'] = 'success'
    orphan_grace_seconds: int = Field(86400, ge=86400)
    health_file: Path = Path("/tmp/museforge-health.json")

    @field_validator("database_url", "broker_url")
    @classmethod
    def validate_url(cls, value: SecretStr, info):
        try:
            url = make_url(value.get_secret_value())
            allowed = {"postgresql+psycopg"} if info.field_name == "database_url" else {"amqp", "amqps"}
            if url.drivername not in allowed or not url.host or not url.username:
                raise ValueError
        except Exception:
            raise ValueError("expected a configured PostgreSQL psycopg or AMQP service URL") from None
        return value

    @field_validator("artifact_root", "web_dist", "weights_dir", "cache_dir", "health_file",
                     "yue2_model_dir", "yue2_vae_dir", "yue2_runner", "yue2_preflight")
    @classmethod
    def absolute_path(cls, value: Path):
        if not value.is_absolute():
            raise ValueError("path must be absolute")
        return value

    @model_validator(mode="after")
    def validate_limits(self):
        if not self.heartbeat_seconds < self.lease_seconds < self.attempt_deadline_seconds < self.hard_watchdog_seconds:
            raise ValueError("require heartbeat < lease < attempt deadline < hard watchdog")
        if self.broker_timeout_seconds >= self.outbox_claim_seconds:
            raise ValueError("broker timeout must be shorter than outbox claim")
        if not self.mock_test_enabled and (self.mock_test_scenarios or self.mock_test_delay_seconds or self.mock_test_outcome != 'success'):
            raise ValueError("mock test controls require explicit test mode")
        if self.music_provider == "mock":
            if self.device != "cpu" or self.model_id or self.model_revision or self.decoder_revision:
                raise ValueError("mock provider requires CPU and no model identity")
        else:
            if self.device != "cuda" or self.precision != "bfloat16":
                raise ValueError("yue2 requires CUDA and bfloat16 precision")
            if self.lyrics_provider != "user":
                raise ValueError("yue2 requires LYRICS_PROVIDER=user")
            if not self.model_id or not self.model_revision or not self.decoder_revision:
                raise ValueError("yue2 requires model, model revision, and decoder revision")
        return self

    @property
    def provider_id(self) -> str:
        return self.music_provider

    @property
    def provider_revision(self) -> str:
        return "1" if self.music_provider == "mock" else "yue2-infer-0.1.5"

    @property
    def provider_route(self) -> str:
        return self.mock_queue if self.music_provider == "mock" else self.yue2_queue

    @property
    def worker_role(self) -> str:
        return "worker-mock" if self.music_provider == "mock" else "worker-yue2"
