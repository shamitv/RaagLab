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
