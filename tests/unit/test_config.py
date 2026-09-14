import pytest
from pydantic import ValidationError
from museforge.config import Settings


@pytest.mark.parametrize('values', [
    {'database_url': 'sqlite:///local.db'}, {'broker_url': 'redis://localhost/0'},
    {'app_port': 80}, {'app_bind': '0.0.0.0'}, {'artifact_root': '../artifacts'},
    {'music_provider': 'real'}, {'device': 'cuda'}, {'model_id': 'not-installed'},
    {'heartbeat_seconds': 30}, {'lease_seconds': 80}, {'worker_concurrency': 2},
    {'duration_seconds': 31}, {'max_attempts': 0},
])
def test_invalid_configuration_fails(values):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)


def test_secret_urls_are_not_in_repr():
    settings = Settings(_env_file=None, database_url='postgresql+psycopg://user:secret-test-value@db/app')
    assert 'secret-test-value' not in repr(settings)
    assert settings.lyrics_provider == settings.music_provider == 'mock'


def test_documented_environment_defaults_load():
    from pathlib import Path
    settings = Settings(_env_file=Path(__file__).resolve().parents[2] / '.env.example')
    assert settings.worker_concurrency == 1
    assert settings.app_port == 8000


def test_yue2_configuration_selects_real_route():
    settings = Settings(_env_file=None, music_provider='yue2', lyrics_provider='user', device='cuda',
                        precision='bfloat16', model_id='m-a-p/YuE2-3B', model_revision='model',
                        decoder_revision='vae')
    assert settings.provider_route == 'museforge.yue2.v1'
    assert settings.worker_role == 'worker-yue2'


def test_yue2_requires_explicit_user_lyrics_mode():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, music_provider='yue2', device='cuda', precision='bfloat16',
                 model_id='m-a-p/YuE2-3B', model_revision='model', decoder_revision='vae')


@pytest.mark.parametrize('lyrics_provider', ['user', 'static', 'mock'])
def test_lyrics_source_configuration_is_independent_for_mock_music(lyrics_provider):
    settings = Settings(_env_file=None, music_provider='mock', lyrics_provider=lyrics_provider)
    assert settings.music_provider == 'mock'
    assert settings.lyrics_provider == lyrics_provider
    assert settings.provider_route == 'museforge.mock.v1'


@pytest.mark.parametrize('values', [
    {'music_provider': 'unknown'},
    {'lyrics_provider': 'unknown'},
    {'music_provider': 'yue2', 'lyrics_provider': 'mock'},
    {'music_provider': 'yue2', 'lyrics_provider': 'static'},
    {'music_provider': 'yue2', 'device': 'mps'},
    {'music_provider': 'yue2', 'precision': 'float32'},
    {'music_provider': 'yue2', 'model_revision': None},
])
def test_provider_configuration_rejects_missing_or_incompatible_adapter(values):
    base = dict(
        _env_file=None,
        music_provider='yue2',
        lyrics_provider='user',
        device='cuda',
        precision='bfloat16',
        model_id='m-a-p/YuE2-3B',
        model_revision='model',
        decoder_revision='vae',
    )
    if values.get('music_provider') == 'unknown':
        base.update(music_provider='unknown')
    if values.get('lyrics_provider') == 'unknown':
        base.update(lyrics_provider='unknown')
    base.update(values)
    with pytest.raises(ValidationError):
        Settings(**base)
