"""Phase 04 library, project organization, settings, and template contracts."""
import time
from uuid import uuid4

import httpx
import pytest

from test_generation_pipeline import BASE, submit, wait


def get(path):
    response = httpx.get(BASE + path)
    response.raise_for_status()
    return response.json()


def patch(path, body, revision):
    return httpx.patch(BASE + path, json=body, headers={'If-Match': f'"{revision}"'})


def test_project_search_archive_and_filter_bound_cursor():
    prefix = 'Phase4 searchable ' + uuid4().hex[:10]
    created = [httpx.post(BASE + '/api/v1/projects', json={'title': f'{prefix} {index}'}).json()
               for index in range(3)]
    first = get(f'/api/v1/projects?q={prefix.replace(" ", "%20")}&limit=1')
    assert first['next_cursor']
    second = get(f'/api/v1/projects?q={prefix.replace(" ", "%20")}&limit=1&cursor={first["next_cursor"]}')
    assert len(first['items']) == len(second['items']) == 1
    assert first['items'][0]['id'] != second['items'][0]['id']
    assert httpx.get(BASE + '/api/v1/projects', params={'q': prefix, 'archived': 'all', 'limit': 1,
        'cursor': first['next_cursor']}).status_code == 422
    assert {item['id'] for item in created} >= {first['items'][0]['id'], second['items'][0]['id']}


def test_duplicate_remaps_history_and_shares_audio():
    accepted, inputs = submit(brief='Phase4 duplicate graph ' + uuid4().hex[:8])
    original_job, _ = wait(accepted)
    original = get(original_job['version_url'])
    project_path = '/api/v1/projects/' + original['project_id']
    iteration_inputs = {key: original['inputs'][key] for key in (
        'brief', 'instruments', 'mood', 'language', 'genre', 'tempo', 'vocal_type', 'lyrics',
        'duration_seconds', 'seed', 'iteration_instruction',
    ) if key in original['inputs']}
    iteration_inputs.update(brief='Phase4 duplicate graph child', iteration_instruction='A linked child')
    accepted_child = httpx.post(
        BASE + f'/api/v1/versions/{original["id"]}/iterations',
        json={'operation': 'variation', 'inputs': iteration_inputs},
        headers={'Idempotency-Key': str(uuid4())},
    )
    assert accepted_child.status_code == 202, accepted_child.text
    child_job, _ = wait(accepted_child.json())
    child = get(child_job['version_url'])

    duplicate = httpx.post(BASE + project_path + '/duplicate')
    assert duplicate.status_code == 201, duplicate.text
    copy = duplicate.json()
    assert copy['id'] != original['project_id']
    assert copy['title'].startswith('Copy of ')
    assert copy['active_version_id'] is not None
    copied = get('/api/v1/projects/' + copy['id'] + '/versions')['items']
    by_number = {item['number']: item for item in copied}
    assert len(copied) == 2
    assert {item['id'] for item in copied}.isdisjoint({original['id'], child['id']})
    assert by_number[original['number']]['parent_version_id'] is None
    assert by_number[child['number']]['parent_version_id'] == by_number[original['number']]['id']
    assert by_number[original['number']]['origin_version_id'] == original['id']
    assert by_number[child['number']]['origin_version_id'] == child['id']
    assert by_number[original['number']]['generation_job_id'] is None
    assert get(f'/api/v1/versions/{by_number[original["number"]]["id"]}')['audio']['id'] == original['audio']['id']
    assert get('/api/v1/projects/' + copy['id'])['jobs'] == []


def test_archive_rejects_active_jobs_and_can_be_undone():
    accepted, _ = submit(seed=4294967203, brief='Phase4 archive race')
    deadline = time.monotonic() + 20
    while get(accepted['status_url'])['state'] != 'running':
        assert time.monotonic() < deadline
        time.sleep(.1)
    path = '/api/v1/projects/' + accepted['project_id']
    project = get(path)
    assert patch(path, {'archived': True}, project['revision']).status_code == 409
    assert httpx.post(BASE + accepted['status_url'] + '/cancel').status_code == 202
    wait(accepted, 'cancelled')
    project = get(path)
    archived = patch(path, {'archived': True}, project['revision'])
    assert archived.status_code == 200 and archived.json()['archived_at']
    assert httpx.get(BASE + '/api/v1/projects', params={'q': 'Phase4 archive race'}).json()['items'] == []
    assert len(httpx.get(BASE + '/api/v1/projects', params={'q': 'Phase4 archive race', 'archived': 'archived'}).json()['items']) == 1
    restored = patch(path, {'archived': False}, archived.json()['revision'])
    assert restored.status_code == 200 and restored.json()['archived_at'] is None


def test_library_filters_search_and_cursor():
    token = uuid4().hex[:10]
    first_job, _ = submit(brief=f'Phase4 library {token}')
    completed, _ = wait(first_job)
    first_version = get(completed['version_url'])
    labeled = patch(completed['version_url'], {'label': f'Library token {token}', 'favorite': True}, first_version['revision'])
    assert labeled.status_code == 200
    inputs = {key: first_version['inputs'][key] for key in (
        'brief', 'instruments', 'mood', 'language', 'genre', 'tempo', 'vocal_type', 'lyrics',
        'duration_seconds', 'seed', 'iteration_instruction',
    ) if key in first_version['inputs']}
    child = httpx.post(BASE + f'/api/v1/versions/{first_version["id"]}/iterations',
        json={'operation': 'variation', 'inputs': inputs}, headers={'Idempotency-Key': str(uuid4())})
    assert child.status_code == 202, child.text
    child_job, _ = wait(child.json())
    child_version = get(child_job['version_url'])
    assert patch(child_job['version_url'], {'favorite': True}, child_version['revision']).status_code == 200

    query = {'q': token, 'favorite_only': 'true', 'genre': first_version['inputs']['genre'],
             'language': first_version['inputs']['language'], 'limit': 1}
    page_one = httpx.get(BASE + '/api/v1/library', params=query)
    assert page_one.status_code == 200, page_one.text
    first_page = page_one.json()
    assert len(first_page['items']) == 1 and first_page['next_cursor']
    query['cursor'] = first_page['next_cursor']
    page_two = httpx.get(BASE + '/api/v1/library', params=query)
    assert page_two.status_code == 200, page_two.text
    assert len(page_two.json()['items']) == 1
    assert page_one.json()['items'][0]['version_id'] != page_two.json()['items'][0]['version_id']
    query['language'] = 'Tamil'
    assert httpx.get(BASE + '/api/v1/library', params=query).status_code == 422


def test_settings_revision_and_template_catalogue():
    current = httpx.get(BASE + '/api/v1/settings')
    assert current.status_code == 200
    original = current.json()
    assert original['generation_defaults']['instruments'] == ['Piano']
    assert original['volume'] == .8 and original['repeat_mode'] == 'off' and original['export_format'] == 'wav'
    assert httpx.patch(BASE + '/api/v1/settings', json={'volume': .5}).status_code == 428
    changed = httpx.patch(BASE + '/api/v1/settings', json={'volume': .5, 'repeat_mode': 'all'},
        headers={'If-Match': current.headers['etag']})
    assert changed.status_code == 200 and changed.json()['volume'] == .5
    assert httpx.patch(BASE + '/api/v1/settings', json={'volume': .3}, headers={'If-Match': current.headers['etag']}).status_code == 412
    listed = get('/api/v1/templates')
    assert len(listed['items']) == 5
    assert all(item['revision'] == 1 for item in listed['items'])
    assert get('/api/v1/templates/quiet-acoustic')['draft']['genre'] == 'Folk'
    assert httpx.get(BASE + '/api/v1/templates/missing').status_code == 404
    restore = httpx.patch(BASE + '/api/v1/settings', json={
        'generation_defaults': original['generation_defaults'], 'volume': original['volume'],
        'repeat_mode': original['repeat_mode'], 'export_format': original['export_format'],
    }, headers={'If-Match': changed.headers['etag']})
    assert restore.status_code == 200
