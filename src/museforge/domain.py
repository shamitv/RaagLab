"""Versioned public intent and provider contracts."""
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

INSTRUMENTS = ['Guitar', 'Piano', 'Tabla', 'Drums', 'Bass', 'Strings', 'Synth']
MOODS = ['Happy', 'Melancholic', 'Romantic', 'Energetic', 'Calm', 'Epic']
LANGUAGES = ['Hindi', 'English', 'Hinglish', 'Punjabi', 'Tamil']
GENRES = ['Indie Pop', 'Pop', 'Folk', 'Ambient', 'Rock', 'Electronic']
WARNING = 'Original instrumental demo; does not faithfully implement musical controls or sing lyrics.'
YUE2_WARNING = ('YuE2 real output is validated technical audio; it may contain vocals even when the '
                'accepted request field is Instrumental. Lyric adherence, language coverage, and '
                'requested duration are not guaranteed.')

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


class CapabilityAssessment(StrictModel):
    """Evidence-backed product capability for one provider revision."""

    state: Literal['supported', 'unsupported', 'unknown']
    evidence: str
    limits: list[str] = Field(default_factory=list)


def capability_matrix(provider='mock'):
    """Keep request acceptance separate from verified model behavior."""
    common = {
        'lyrics_text_input': CapabilityAssessment(
            state='supported',
            evidence='The API accepts and preserves non-empty user-supplied lyrics.',
        ),
        'technical_audio_output': CapabilityAssessment(
            state='supported',
            evidence='Generated files are decoded, checked, and validated before atomic publication.',
            limits=['Valid audio metadata does not establish musical quality or semantic control fidelity.'],
        ),
        'audio_conditioning': CapabilityAssessment(
            state='unsupported', evidence='No provider route accepts a reference-audio input.'
        ),
        'audio_editing': CapabilityAssessment(
            state='unsupported', evidence='No provider route edits an existing audio artifact.'
        ),
        'continuation': CapabilityAssessment(
            state='unsupported', evidence='No provider route continues from an existing audio artifact.'
        ),
    }
    if provider == 'yue2':
        return common | {
            'lyrics_text_generation': CapabilityAssessment(
                state='unsupported', evidence='YuE2 consumes supplied lyrics; it does not generate a separate lyrics result.'
            ),
            'instrumental_music_generation': CapabilityAssessment(
                state='unknown',
                evidence='The application accepts an Instrumental request, but the generated result has not been audited for instrumental-only output.',
                limits=['The model may include vocals.'],
            ),
            'vocal_generation': CapabilityAssessment(
                state='unknown',
                evidence='The model may include vocals; vocal presence and behavior have not been audited.',
            ),
            'exact_lyrics_singing': CapabilityAssessment(
                state='unknown',
                evidence='User lyrics are passed to the model, but lyric adherence has not been measured.',
            ),
            'language_fidelity': CapabilityAssessment(
                state='unknown',
                evidence='Only English user lyrics have been exercised through the application route; audio language fidelity is unverified.',
            ),
            'instrument_control': CapabilityAssessment(
                state='unknown', evidence='Instrument selections are included in the style prompt; output fidelity has not been measured.'
            ),
            'mood_control': CapabilityAssessment(
                state='unknown', evidence='Mood selection is included in the style prompt; output fidelity has not been measured.'
            ),
            'genre_control': CapabilityAssessment(
                state='unknown', evidence='Genre selection is included in the style prompt; output fidelity has not been measured.'
            ),
            'tempo_control': CapabilityAssessment(
                state='unknown', evidence='Tempo selection is included in the style prompt; output fidelity has not been measured.'
            ),
            'duration_control': CapabilityAssessment(
                state='unsupported',
                evidence='The request duration is retained as intent but does not constrain YuE2 output duration.',
                limits=['Actual output duration is model-determined and may exceed the requested value.'],
            ),
            'seed_reproducibility': CapabilityAssessment(
                state='unknown', evidence='The seed is passed to YuE2; cross-runtime reproducibility is unverified.'
            ),
        }
    return common | {
        'lyrics_text_generation': CapabilityAssessment(
            state='supported',
            evidence='The mock lyrics provider returns deterministic demo text, an original static fixture, or supplied user text.',
            limits=['Generated text is scripted demo content, not model-written lyrics.'],
        ),
        'instrumental_music_generation': CapabilityAssessment(
            state='unsupported',
            evidence='The mock provider creates labelled demo tones, not semantically conditioned instrumental music.',
        ),
        'vocal_generation': CapabilityAssessment(
            state='unsupported', evidence='The mock provider creates no sung vocals.'
        ),
        'exact_lyrics_singing': CapabilityAssessment(
            state='unsupported', evidence='The mock provider does not sing supplied lyrics.'
        ),
        'language_fidelity': CapabilityAssessment(
            state='unsupported', evidence='The mock audio contains no linguistic content.'
        ),
        'instrument_control': CapabilityAssessment(
            state='unsupported', evidence='Instrument selections do not alter mock audio.'
        ),
        'mood_control': CapabilityAssessment(
            state='unsupported', evidence='Mood selection does not alter mock audio.'
        ),
        'genre_control': CapabilityAssessment(
            state='unsupported', evidence='Genre selection does not alter mock audio.'
        ),
        'tempo_control': CapabilityAssessment(
            state='unsupported', evidence='Tempo selection does not alter mock audio.'
        ),
        'duration_control': CapabilityAssessment(
            state='supported', evidence='Mock audio is generated at the requested duration.'
        ),
        'seed_reproducibility': CapabilityAssessment(
            state='supported', evidence='The same generation snapshot and seed produce identical mock PCM.'
        ),
    }


def capabilities(provider='mock', *, model_id=None, model_revision=None, decoder_revision=None):
    matrix = {
        name: assessment.model_dump(mode='json')
        for name, assessment in capability_matrix(provider).items()
    }
    if provider == 'yue2':
        return dict(provider_id='yue2', provider_revision='yue2-infer-0.1.6', model_id=model_id,
                    model_revision=model_revision, decoder_revision=decoder_revision, is_demo=False,
                    capability_matrix=matrix, lyrics_modes=['user'], lyrics_text=True,
                    text_to_instrumental=None, vocals=None, exact_lyrics_vocals=None, instruments=INSTRUMENTS,
                    moods=MOODS, languages=['English'], genres=GENRES, vocal_types=['Instrumental'],
                    operations=['generate'], duration={'min': 5, 'max': 30, 'default': 8},
                    sample_rates=[48000], channels=[2],
                    seed_behavior='seed is passed to YuE2; cross-runtime determinism is unverified',
                    cooperative_cancel=True, progress_mode='stage', warnings=[YUE2_WARNING,
                    'YuE2 duration is model-determined and may exceed the requested duration.',
                    'Only English user lyrics have been exercised through the application route.',
                    'Refinement, variation, regeneration, audio editing, and continuation are unsupported.'])
    return dict(provider_id='mock', provider_revision='1', model_id=None, model_revision=None,
                decoder_revision=None, is_demo=True, capability_matrix=matrix,
                lyrics_modes=['user', 'static', 'mock'], lyrics_text=True,
                text_to_instrumental=False, vocals=False, exact_lyrics_vocals=False,
                instruments=INSTRUMENTS, moods=MOODS, languages=LANGUAGES, genres=GENRES,
                vocal_types=['Instrumental'], operations=['generate', 'refine', 'variation', 'regenerate', 'lyrics_edit'], duration={'min': 5, 'max': 30, 'default': 8},
                sample_rates=[44100], channels=[2], seed_behavior='deterministic PCM for identical snapshot',
                cooperative_cancel=True, progress_mode='stage', warnings=[WARNING])


def provider_capabilities(settings):
    result = capabilities(settings.music_provider, model_id=settings.model_id,
                         model_revision=settings.model_revision,
                         decoder_revision=settings.decoder_revision) | {'provider_route': settings.provider_route}
    if settings.yue2_test_smoke:
        result['warnings'].append('TEST SMOKE MODE: deliberately short/truncated audio; not a completed song.')
    return result

# Response contracts are generated into the browser client from OpenAPI.
from datetime import datetime
from typing import Any

class ReadinessInfo(StrictModel):
    state: str
    last_observed_at: datetime | None
    device: str | None = None
    fallback_reason: str | None = None

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
    operation: str
    retry_of_job_id: UUID | None
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

class LibraryItem(StrictModel):
    project_id: UUID
    project_title: str
    version_id: UUID
    version_number: int
    version_label: str
    favorite: bool
    created_at: datetime
    genre: str | None
    language: str | None
    duration_seconds: float | None
    available: bool

class LibraryPage(StrictModel):
    items: list[LibraryItem]
    next_cursor: str | None

class GenerationDefaults(StrictModel):
    instruments: list[Literal['Guitar', 'Piano', 'Tabla', 'Drums', 'Bass', 'Strings', 'Synth']] = Field(default_factory=lambda: ['Piano'], min_length=1)
    mood: Literal['Happy', 'Melancholic', 'Romantic', 'Energetic', 'Calm', 'Epic'] = 'Calm'
    language: Literal['Hindi', 'English', 'Hinglish', 'Punjabi', 'Tamil'] = 'English'
    genre: Literal['Indie Pop', 'Pop', 'Folk', 'Ambient', 'Rock', 'Electronic'] = 'Indie Pop'
    tempo: Literal['Slow', 'Medium', 'Fast'] = 'Medium'
    vocal_type: Literal['Instrumental'] = 'Instrumental'
    duration_seconds: int = Field(8, ge=5, le=30)
    lyrics_mode: Literal['user', 'static', 'mock'] = 'mock'

    @field_validator('instruments')
    @classmethod
    def unique_instruments(cls, value):
        if len(value) != len(set(value)):
            raise ValueError('Instruments must be unique')
        return value

class SettingsPatch(StrictModel):
    generation_defaults: GenerationDefaults | None = None
    volume: float | None = Field(None, ge=0, le=1)
    repeat_mode: Literal['off', 'one', 'all'] | None = None
    export_format: Literal['wav'] | None = None

    @model_validator(mode='after')
    def validate_patch(self):
        if not self.model_fields_set: raise ValueError('Patch must not be empty')
        for name in self.model_fields_set:
            if getattr(self, name) is None: raise ValueError(f'{name} is required')
        return self

class SettingsView(StrictModel):
    revision: int
    generation_defaults: GenerationDefaults
    volume: float
    repeat_mode: Literal['off', 'one', 'all']
    export_format: Literal['wav']

class TemplateView(StrictModel):
    id: str
    revision: int
    name: str
    description: str
    draft: dict[str, Any]

class TemplatePage(StrictModel):
    items: list[TemplateView]

class LyricsCheckpoint(StrictModel):
    text: str
    source: Literal['user', 'static', 'mock']
    provider_revision: str
    fixture_id: str | None
    fixture_revision: str | None

class CapabilitiesView(StrictModel):
    provider_id: str
    provider_revision: str
    provider_route: str | None = None
    model_id: str | None
    model_revision: str | None
    decoder_revision: str | None = None
    is_demo: bool
    capability_matrix: dict[str, CapabilityAssessment]
    lyrics_modes: list[str]
    lyrics_text: bool
    text_to_instrumental: bool | None
    vocals: bool | None
    exact_lyrics_vocals: bool | None
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
    # Existing immutable versions predate the evidence matrix.
    capability_matrix: dict[str, CapabilityAssessment] = Field(default_factory=dict)
    lyrics: LyricsCheckpoint
    runtime: dict[str, Any] = Field(default_factory=dict)

class VersionView(StrictModel):
    favorite: bool = False
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


class ProjectPatch(StrictModel):
    title: str | None = None
    draft: Generation | None = None
    active_version_id: UUID | None = None
    archived: bool | None = None

    @model_validator(mode='after')
    def validate_patch(self):
        if not self.model_fields_set: raise ValueError('Patch must not be empty')
        if 'title' in self.model_fields_set: ProjectCreate(title=self.title)
        if 'draft' in self.model_fields_set and self.draft is None: raise ValueError('Draft is required')
        if 'archived' in self.model_fields_set and self.archived is None: raise ValueError('Archive state is required')
        return self

class VersionPatch(StrictModel):
    label: str | None = None
    favorite: bool | None = None

    @model_validator(mode='after')
    def validate_patch(self):
        if not self.model_fields_set: raise ValueError('Patch must not be empty')
        if 'label' in self.model_fields_set: ProjectCreate(title=self.label)
        if 'favorite' in self.model_fields_set and self.favorite is None: raise ValueError('Favorite is required')
        return self

class Iteration(StrictModel):
    operation: Literal['refine', 'variation', 'regenerate', 'lyrics_edit']
    inputs: Generation

    @model_validator(mode='after')
    def validate_operation(self):
        if self.operation == 'refine' and not self.inputs.iteration_instruction:
            raise ValueError('Refinement instruction is required')
        if self.operation == 'lyrics_edit' and self.inputs.lyrics.mode != 'user':
            raise ValueError('Lyrics edit requires exact user text')
        return self
