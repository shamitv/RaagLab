"""Versioned public intent and provider contracts."""
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

INSTRUMENTS = ['Guitar', 'Piano', 'Tabla', 'Drums', 'Bass', 'Strings', 'Synth']
MOODS = ['Happy', 'Melancholic', 'Romantic', 'Energetic', 'Calm', 'Epic']
LANGUAGES = ['Hindi', 'English', 'Hinglish', 'Punjabi', 'Tamil']
GENRES = ['Indie Pop', 'Pop', 'Folk', 'Ambient', 'Rock', 'Electronic']
WARNING = 'Original instrumental demo; does not faithfully implement musical controls or sing lyrics.'

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Lyrics(StrictModel):
    mode: Literal['user', 'static', 'mock'] = 'mock'
    text: str | None = None

    @model_validator(mode='after')
    def validate_text(self):
        if self.mode == 'user' and (self.text is None or not self.text.strip()):
            raise ValueError('User lyrics are required')
        if self.text is not None:
            if '\x00' in self.text: raise ValueError('NUL is not supported in stored text')
            if len(self.text) > 20000 or len(self.text.encode('utf-8')) > 80000:
                raise ValueError('Lyrics exceed limits')
        return self

class Generation(StrictModel):
    project_id: UUID | None = None
    brief: str = Field(min_length=1, max_length=500)
    instruments: list[Literal['Guitar', 'Piano', 'Tabla', 'Drums', 'Bass', 'Strings', 'Synth']] = Field(min_length=1)
    mood: Literal['Happy', 'Melancholic', 'Romantic', 'Energetic', 'Calm', 'Epic']
    language: Literal['Hindi', 'English', 'Hinglish', 'Punjabi', 'Tamil'] = 'English'
    genre: Literal['Indie Pop', 'Pop', 'Folk', 'Ambient', 'Rock', 'Electronic'] = 'Indie Pop'
    tempo: Literal['Slow', 'Medium', 'Fast'] = 'Medium'
    vocal_type: Literal['Instrumental'] = 'Instrumental'
    lyrics: Lyrics = Field(default_factory=Lyrics)
    duration_seconds: int = Field(8, ge=5, le=30, strict=True)
    seed: int | None = Field(None, ge=0, le=4294967295, strict=True)
    iteration_instruction: str | None = Field(None, max_length=2000)

    @field_validator('brief', 'iteration_instruction')
    @classmethod
    def valid_unicode(cls, value):
        if value is not None:
            value.encode('utf-8')
            if '\x00' in value: raise ValueError('NUL is not supported in stored text')
            if not value.strip():
                raise ValueError('Text must not be blank')
        return value

    @field_validator('instruments')
    @classmethod
    def unique(cls, value):
        if len(value) != len(set(value)):
            raise ValueError('Instruments must be unique')
        return value

class ProjectCreate(StrictModel):
    title: str = Field(default='Untitled project', min_length=1, max_length=120)
    draft: Generation | None = None

    @field_validator('title')
    @classmethod
    def nonblank(cls, value):
        value.encode('utf-8')
        if '\x00' in value: raise ValueError('NUL is not supported in stored text')
        if not value.strip():
            raise ValueError('Title must not be blank')
        return value

class Accepted(StrictModel):
    job_id: UUID
    project_id: UUID
    state: str
    status_url: str
    project_url: str

class ProviderError(Exception):
    def __init__(self, code: str, retryable: bool = False):
        self.code, self.retryable = code, retryable
        super().__init__(code)


def capabilities():
    return dict(provider_id='mock', provider_revision='1', model_id=None, model_revision=None,
                is_demo=True, lyrics_modes=['user', 'static', 'mock'], lyrics_text=True,
                text_to_instrumental=False, vocals=False, exact_lyrics_vocals=False,
                instruments=INSTRUMENTS, moods=MOODS, languages=LANGUAGES, genres=GENRES,
                vocal_types=['Instrumental'], operations=['generate'], duration={'min': 5, 'max': 30, 'default': 8},
                sample_rates=[44100], channels=[2], seed_behavior='deterministic PCM for identical snapshot',
                cooperative_cancel=True, progress_mode='stage', warnings=[WARNING])

# Response contracts are generated into the browser client from OpenAPI.
from datetime import datetime
from typing import Any

class ReadinessInfo(StrictModel):
    state: str
    last_observed_at: datetime | None

class SafeJobError(StrictModel):
    code: str
    message: str
    retryable: bool

class AttemptView(StrictModel):
    attempt_number: int
    worker_id: UUID
    started_at: datetime
    ended_at: datetime | None
    outcome: str | None

class JobView(StrictModel):
    id: UUID
    project_id: UUID
    state: str
    stage: str
    progress: float | None
    attempt_count: int
    cancellation_requested_at: datetime | None
    result_version_id: UUID | None
    created_at: datetime
    completed_at: datetime | None
    correlation_id: UUID
    dispatch_sequence: int
    error: SafeJobError | None
    version_url: str | None
    dispatch_status: str
    attempts: list[AttemptView]
    provider_readiness: ReadinessInfo

class ProjectView(StrictModel):
    id: UUID
    workspace_id: UUID
    created_at: datetime
    title: str
    draft: dict[str, Any]
    revision: int
    active_version_id: UUID | None
    selection_epoch: int
    latest_submission_seq: int
    next_version_number: int
    archived_at: datetime | None

class ProjectDetail(ProjectView):
    jobs: list[JobView]

class ProjectPage(StrictModel):
    items: list[ProjectView]
    next_cursor: str | None

class LyricsCheckpoint(StrictModel):
    text: str
    source: Literal['user', 'static', 'mock']
    provider_revision: str
    fixture_id: str | None
    fixture_revision: str | None

class CapabilitiesView(StrictModel):
    provider_id: str
    provider_revision: str
    model_id: str | None
    model_revision: str | None
    is_demo: bool
    lyrics_modes: list[str]
    lyrics_text: bool
    text_to_instrumental: bool
    vocals: bool
    exact_lyrics_vocals: bool
    instruments: list[str]
    moods: list[str]
    languages: list[str]
    genres: list[str]
    vocal_types: list[str]
    operations: list[str]
    duration: dict[str, int]
    sample_rates: list[int]
    channels: list[int]
    seed_behavior: str
    cooperative_cancel: bool
    progress_mode: str
    warnings: list[str]

class CapabilitiesResponse(CapabilitiesView):
    default_lyrics_mode: Literal['user', 'static', 'mock']
    readiness: ReadinessInfo

class Provenance(CapabilitiesView):
    lyrics: LyricsCheckpoint

class VersionView(StrictModel):
    id: UUID
    workspace_id: UUID
    created_at: datetime
    project_id: UUID
    parent_version_id: UUID | None
    origin_version_id: UUID | None
    generation_job_id: UUID | None
    number: int
    label: str
    revision: int
    inputs: dict[str, Any]
    lyrics: str
    structure: dict[str, Any] | None
    provenance: Provenance
    snapshot_schema_version: int
    audio_recomposed: bool

class AudioView(StrictModel):
    id: UUID
    created_at: datetime
    sha256: str
    byte_size: int
    media_type: str
    sample_rate: int
    channels: int
    duration_seconds: float
    published_at: datetime
    available_at: datetime | None
    retired_at: datetime | None
    url: str

class VersionDetail(VersionView):
    audio: AudioView

class VersionPage(StrictModel):
    items: list[VersionView]
    next_cursor: str | None

class ErrorField(StrictModel):
    field: str
    code: str

class ErrorResponse(StrictModel):
    code: str
    message: str
    retryable: bool
    correlation_id: str
    fields: list[ErrorField] | None = None
