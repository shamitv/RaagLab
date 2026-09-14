from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

TASK_NAME = "museforge.execute_generation"


class GenerationEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    message_id: UUID
    job_id: UUID
    correlation_id: UUID
    dispatch_sequence: int = Field(gt=0)
    dispatched_at: AwareDatetime
    provider_route: str = Field(min_length=1, max_length=128)
