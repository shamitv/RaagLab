import os
import re
from uuid import uuid4
import httpx


def test_compiled_shell_and_missing_resources():
    with httpx.Client(base_url=os.environ['API_BASE_URL'], timeout=10) as client:
        index = client.get('/')
        assert index.status_code == 200
        assert index.headers['cache-control'] == 'no-cache'
        assert '/src/main.tsx' not in index.text
        assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', index.text)
        assert assets
        for asset in assets:
            response = client.get(asset)
            assert response.status_code == 200
            assert 'immutable' in response.headers['cache-control']
        assert client.get(f'/projects/{uuid4()}').text == index.text
        for path in ('/api/v1/missing', '/assets/missing.js', '/health/missing', '/not-a-route'):
            assert client.get(path).status_code == 404
        assert client.get('/openapi.json').json()['info']['title'] == 'MuseForge AI'
