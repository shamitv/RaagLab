"""Conditional metadata and immutable iterations across the real worker pipeline."""
from uuid import uuid4
import httpx
import pytest
from test_generation_pipeline import BASE, TEXT, submit, wait


def get(path):
    r = httpx.get(BASE + path); r.raise_for_status(); return r.json()


def patch(path, body, revision=None):
    return httpx.patch(BASE + path, json=body, headers={} if revision is None else {'If-Match': f'"{revision}"'})


@pytest.mark.parametrize('operation', ['regenerate', 'variation', 'refine', 'lyrics_edit'])
def test_iteration_parentage_and_selection(operation):
    accepted, inputs = submit()
    job, _ = wait(accepted)
    source = get(job['version_url'])
    project_path = '/api/v1/projects/' + source['project_id']
    path = '/api/v1/versions/' + source['id'] + '/iterations'
    inputs.update(iteration_instruction='A quieter original demo', lyrics={'mode': 'user', 'text': TEXT + '  exact edit\n'})
    body = {'operation': operation, 'inputs': inputs}
    headers = {'Idempotency-Key': str(uuid4())}
    r = httpx.post(BASE + path, json=body, headers=headers)
    assert r.status_code == 202, r.text
    assert httpx.post(BASE + path, json=body, headers=headers).json()['job_id'] == r.json()['job_id']
    body['inputs']['brief'] = 'Conflicting reuse'
    assert httpx.post(BASE + path, json=body, headers=headers).status_code == 409
    project = get(project_path)
    selected = patch(project_path, {'active_version_id': source['id']}, project['revision'])
    assert selected.status_code == 200
    result, _ = wait(r.json())
    child = get(result['version_url'])
    assert child['parent_version_id'] == source['id']
    assert child['inputs']['operation'] == operation
    assert child['inputs']['iteration_instruction'] == 'A quieter original demo'
    assert child['lyrics'] == TEXT + '  exact edit\n'
    assert child['audio_recomposed'] is (operation != 'lyrics_edit')
    assert (child['audio']['id'] == source['audio']['id']) is (operation == 'lyrics_edit')
    assert get(project_path)['active_version_id'] == source['id']
    assert get(job['version_url'])['lyrics'] == TEXT


def test_conditional_metadata_and_cross_project_selection():
    accepted, inputs = submit()
    job, _ = wait(accepted)
    source = get(job['version_url'])
    path = '/api/v1/projects/' + source['project_id']
    project = get(path)
    assert patch(path, {'title': 'New title'}).status_code == 428
    r = patch(path, {'title': 'New title', 'draft': inputs}, project['revision'])
    assert r.status_code == 200
    assert r.headers['etag'] == f'"{project["revision"] + 1}"'
    assert patch(path, {'title': 'Stale'}, project['revision']).status_code == 412
    other = httpx.post(BASE + '/api/v1/projects', json={}).json()
    assert patch('/api/v1/projects/' + other['id'], {'active_version_id': source['id']}, other['revision']).status_code == 422
    vpath = job['version_url']
    assert patch(vpath, {'label': 'Exact name', 'favorite': True}, source['revision']).status_code == 200
    updated = get(vpath)
    assert updated['favorite'] and updated['label'] == 'Exact name'
    assert patch(vpath, {'favorite': False}, source['revision']).status_code == 412
    assert patch(vpath, {'lyrics': 'Overwrite'}, updated['revision']).status_code == 422
    assert patch(vpath, {'favorite': False}, updated['revision']).status_code == 200
    assert not get(vpath)['favorite']
