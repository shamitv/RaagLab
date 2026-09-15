from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from museforge.api.app import create_app
from museforge.config import Settings


@pytest.fixture
def client(tmp_path):
    web = tmp_path / 'web'
    (web / 'assets').mkdir(parents=True)
    (web / 'index.html').write_text('<!doctype html><title>Foundation</title>')
    (web / 'assets' / 'app-Ab12cd34.js').write_text('export const built = true;')
    (web / 'assets' / 'plain.css').write_text('body {}')
    (web / 'assets' / '.secret').write_text('private')
    outside = tmp_path / 'outside.js'
    outside.write_text('private')
    (web / 'assets' / 'linked-Ab12cd34.js').symlink_to(outside)
    settings = Settings(_env_file=None, web_dist=web, artifact_root=tmp_path,
                        database_url='postgresql+psycopg://user:test@127.0.0.1:1/app')
    with TestClient(create_app(settings)) as client:
        yield client


@pytest.mark.parametrize('path', ['/', '/create', '/projects', '/library', '/songs', '/settings', '/templates', f'/projects/{uuid4()}', f'/songs/{uuid4()}'])
def test_client_refresh_serves_revalidated_html(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']
    assert response.headers['cache-control'] == 'no-cache'


@pytest.mark.parametrize('path', ['/api/v1/missing', '/api', '/health/missing', '/assets/missing.js', '/other',
                                  '/projects/not-a-uuid', '/assets/.secret', '/assets/linked-Ab12cd34.js',
                                  '/assets/%2e%2e/index.html', '/assets/%2fetc/passwd'])
def test_unknown_and_unsafe_paths_do_not_become_html(client, path):
    response = client.get(path)
    assert response.status_code == 404
    assert 'text/html' not in response.headers.get('content-type', '')


def test_asset_cache_policy(client):
    asset = client.get('/assets/app-Ab12cd34.js')
    assert asset.status_code == 200
    assert asset.headers['cache-control'] == 'public, max-age=31536000, immutable'
    assert client.get('/assets/plain.css').headers['cache-control'] == 'no-cache'


def test_documentation_and_health_are_not_intercepted(client):
    assert client.get('/health/live').json() == {'status': 'alive'}
    schema = client.get('/openapi.json').json()
    assert '/health/ready' in schema['paths']
    assert '/api/v1/generations' in schema['paths']
    assert schema['paths']['/api/v1/generations']['post']['responses']['422']['content']['application/json']['schema']['$ref'].endswith('/ErrorResponse')
    for path in ('/docs', '/redoc'):
        assert client.get(path).status_code == 200
    ready = client.get('/health/ready')
    assert ready.status_code == 503
    assert ready.json()['dependencies']['database'] == 'unavailable'
    assert 'postgresql' not in ready.text
