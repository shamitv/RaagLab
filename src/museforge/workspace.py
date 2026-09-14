"""Workspace preferences and original local starter templates."""
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
from museforge.db import schema as db


DEFAULT_GENERATION_DEFAULTS = {
    'instruments': ['Piano'], 'mood': 'Calm', 'language': 'English',
    'genre': 'Indie Pop', 'tempo': 'Medium', 'vocal_type': 'Instrumental',
    'duration_seconds': 8, 'lyrics_mode': 'mock',
}

TEMPLATES = [
    dict(id='quiet-acoustic', revision=1, name='Quiet acoustic',
         description='A gentle folk idea with room to breathe.',
         draft=dict(brief='A gentle acoustic instrumental with a calm, spacious feel.', instruments=['Guitar'], mood='Calm', language='English', genre='Folk', tempo='Slow', vocal_type='Instrumental', lyrics={'mode': 'mock'}, duration_seconds=8)),
    dict(id='bright-indie-pop', revision=1, name='Bright indie pop',
         description='A light, upbeat starting point for a catchy demo.',
         draft=dict(brief='A bright indie pop instrumental with a warm melodic hook.', instruments=['Piano', 'Drums'], mood='Happy', language='English', genre='Indie Pop', tempo='Fast', vocal_type='Instrumental', lyrics={'mode': 'mock'}, duration_seconds=8)),
    dict(id='tabla-evening', revision=1, name='Tabla evening',
         description='A relaxed Indian folk palette led by tabla.',
         draft=dict(brief='A relaxed evening instrumental with a soft tabla pulse.', instruments=['Tabla', 'Strings'], mood='Romantic', language='Hindi', genre='Folk', tempo='Slow', vocal_type='Instrumental', lyrics={'mode': 'mock'}, duration_seconds=8)),
    dict(id='ambient-focus', revision=1, name='Ambient focus',
         description='A calm, minimal bed for a focused mood.',
         draft=dict(brief='A minimal ambient instrumental with a steady, calm texture.', instruments=['Synth', 'Piano'], mood='Calm', language='English', genre='Ambient', tempo='Slow', vocal_type='Instrumental', lyrics={'mode': 'mock'}, duration_seconds=8)),
    dict(id='cinematic-strings', revision=1, name='Cinematic strings',
         description='A dramatic instrumental sketch with a rising arc.',
         draft=dict(brief='A cinematic instrumental with expressive strings and an uplifting arc.', instruments=['Strings', 'Piano'], mood='Epic', language='English', genre='Ambient', tempo='Medium', vocal_type='Instrumental', lyrics={'mode': 'mock'}, duration_seconds=8)),
]


def ensure_settings(connection, settings):
    connection.execute(insert(db.workspace_settings).values(
        workspace_id=settings.workspace_id,
        generation_defaults=DEFAULT_GENERATION_DEFAULTS,
        volume=0.8,
        repeat_mode='off',
        export_format='wav',
    ).on_conflict_do_nothing(index_elements=[db.workspace_settings.c.workspace_id]))
    return connection.execute(db.workspace_settings.select().where(
        db.workspace_settings.c.workspace_id == settings.workspace_id)).mappings().one()


def settings_view(record):
    return {key: record[key] for key in ('revision', 'generation_defaults', 'volume', 'repeat_mode', 'export_format')}


def updated_at():
    return datetime.now(timezone.utc)
