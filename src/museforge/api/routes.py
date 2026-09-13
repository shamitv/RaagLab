"""Workspace-scoped public generation and media endpoints."""
import base64
import os
import json
from datetime import datetime
from uuid import UUID
import sqlalchemy as sa
from fastapi import APIRouter, Header, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.background import BackgroundTask
from museforge.db import schema as db
from museforge.domain import Accepted, Generation, ProjectCreate, ProviderError, capabilities
from museforge.domain import ErrorResponse, CapabilitiesResponse, ProjectView, ProjectDetail, ProjectPage, JobView, VersionPage, VersionDetail
from museforge.jobs import accepted, cancel, row, scoped, submit
from museforge.storage import open_artifact, range_bounds

router = APIRouter(prefix='/api/v1', responses={status: {'model': ErrorResponse}
    for status in (404, 409, 410, 413, 422, 503)})


def context(request): return request.app.state.engine, request.app.state.settings


def page(c, table, settings, limit, cursor, *conditions):
    query = sa.select(table).where(scoped(table, settings), *conditions)
    if cursor:
        try:
            stamp, identifier = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            query = query.where(sa.tuple_(table.c.created_at, table.c.id) > sa.tuple_(datetime.fromisoformat(stamp), UUID(identifier)))
        except Exception: raise ProviderError('invalid_cursor') from None
    rows = [dict(r) for r in c.execute(query.order_by(table.c.created_at, table.c.id).limit(limit + 1)).mappings()]
    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = base64.urlsafe_b64encode(json.dumps([last['created_at'].isoformat(), str(last['id'])]).encode()).decode()
    return dict(items=rows[:limit], next_cursor=next_cursor)


def job_detail(c, settings, identifier):
    job = row(c, db.jobs, identifier, settings)
    result = {k: job[k] for k in ('id', 'project_id', 'state', 'stage', 'progress', 'attempt_count', 'cancellation_requested_at',
        'result_version_id', 'created_at', 'completed_at', 'correlation_id', 'dispatch_sequence')}
    result['error'] = {'code': job['error_code'], 'message': job['error_code'].replace('_', ' '), 'retryable': job['state'] == 'retrying'} if job['error_code'] else None
    result['version_url'] = f"/api/v1/versions/{job['result_version_id']}" if job['result_version_id'] else None
    result['dispatch_status'] = c.scalar(sa.select(db.outbox.c.state).where(db.outbox.c.job_id == identifier,
        db.outbox.c.dispatch_sequence == job['dispatch_sequence']))
    result['attempts'] = [dict(r) for r in c.execute(sa.select(db.attempts.c.attempt_number, db.attempts.c.worker_id,
        db.attempts.c.started_at, db.attempts.c.ended_at, db.attempts.c.outcome).where(db.attempts.c.job_id == identifier)).mappings()]
    result['provider_readiness'] = readiness(c, settings)
    return result


def readiness(c, settings):
    rows = c.execute(sa.select(db.registrations.c.readiness, db.registrations.c.last_heartbeat).where(
        scoped(db.registrations, settings), db.registrations.c.provider_route == settings.mock_queue,
        db.registrations.c.expires_at > sa.func.now()).order_by(db.registrations.c.last_heartbeat.desc())).mappings().all()
    return dict(state=('busy' if any(r['readiness'] == 'busy' for r in rows) else rows[0]['readiness']) if rows else 'offline', last_observed_at=rows[0]['last_heartbeat'] if rows else None)


@router.get('/capabilities', response_model=CapabilitiesResponse)
def get_capabilities(request: Request):
    engine, settings = context(request)
    with engine.connect() as c:
        return dict(capabilities() | {'duration': {'min': 5, 'max': 30, 'default': settings.duration_seconds}}, default_lyrics_mode=settings.lyrics_provider,
                    readiness=readiness(c, settings))


@router.post('/projects', status_code=201, response_model=ProjectView)
def create_project(body: ProjectCreate, request: Request, response: Response):
    engine, settings = context(request)
    with engine.begin() as c:
        project = dict(c.execute(db.projects.insert().values(workspace_id=settings.workspace_id, title=body.title,
            draft=body.draft.model_dump(mode='json') if body.draft else {}).returning(db.projects)).mappings().one())
    response.headers['Location'] = f"/api/v1/projects/{project['id']}"
    response.headers['ETag'] = f'"{project["revision"]}"'
    return project


@router.get('/projects', response_model=ProjectPage)
def projects(request: Request, limit: int = Query(20, ge=1, le=100), cursor: str | None = None):
    engine, settings = context(request)
    with engine.connect() as c: return page(c, db.projects, settings, limit, cursor, db.projects.c.archived_at.is_(None))


@router.get('/projects/{identifier}', response_model=ProjectDetail)
def project(identifier: UUID, request: Request, response: Response):
    engine, settings = context(request)
    with engine.connect() as c:
        result = row(c, db.projects, identifier, settings)
        result['jobs'] = [job_detail(c, settings, i) for i in c.execute(sa.select(db.jobs.c.id).where(
            scoped(db.jobs, settings), db.jobs.c.project_id == identifier).order_by(db.jobs.c.created_at.desc()).limit(100)).scalars().all()]
    response.headers['ETag'] = f'"{result["revision"]}"'
    return result


@router.post('/generations', status_code=202, response_model=Accepted)
def generation(body: Generation, request: Request, response: Response,
               idempotency_key: str = Header(min_length=16, max_length=128)):
    engine, settings = context(request)
    root = settings.artifact_root
    if not root.is_dir() or root.is_symlink() or not os.access(root, os.R_OK | os.X_OK):
        return JSONResponse({'code': 'storage_unavailable', 'message': 'Artifact storage unavailable',
            'retryable': True, 'correlation_id': request.state.correlation_id}, status_code=503)
    result = submit(engine, settings, body, idempotency_key)
    response.headers['Location'] = result['status_url']
    return result


@router.get('/jobs/{identifier}', response_model=JobView)
def job(identifier: UUID, request: Request):
    engine, settings = context(request)
    with engine.connect() as c: return job_detail(c, settings, identifier)


@router.post('/jobs/{identifier}/cancel', response_model=JobView)
def cancel_job(identifier: UUID, request: Request, response: Response):
    engine, settings = context(request)
    result = cancel(engine, settings, identifier)
    response.status_code = 202 if result['state'] == 'cancellation_requested' else 200
    with engine.connect() as c: return job_detail(c, settings, identifier)


@router.get('/projects/{identifier}/versions', response_model=VersionPage)
def versions(identifier: UUID, request: Request, limit: int = Query(20, ge=1, le=100), cursor: str | None = None):
    engine, settings = context(request)
    with engine.connect() as c:
        row(c, db.projects, identifier, settings)
        return page(c, db.versions, settings, limit, cursor, db.versions.c.project_id == identifier)


@router.get('/versions/{identifier}', response_model=VersionDetail)
def version(identifier: UUID, request: Request):
    engine, settings = context(request)
    with engine.connect() as c:
        result = row(c, db.versions, identifier, settings)
        artifact = c.execute(sa.select(db.artifacts).join(db.links, db.links.c.artifact_id == db.artifacts.c.id)
            .where(db.links.c.version_id == identifier, db.links.c.role == 'audio', scoped(db.artifacts, settings))).mappings().one()
        result['audio'] = {k: v for k,v in artifact.items() if k not in ('storage_key', 'workspace_id')}
        result['audio']['url'] = f"/api/v1/artifacts/{artifact['id']}"
        return result


@router.get('/artifacts/{identifier}')
@router.head('/artifacts/{identifier}', include_in_schema=False)
def artifact(identifier: UUID, request: Request):
    engine, settings = context(request)
    with engine.connect() as c: result = row(c, db.artifacts, identifier, settings)
    file = open_artifact(settings.artifact_root, result['storage_key'])
    size = os.fstat(file.fileno()).st_size
    if size != result['byte_size']:
        file.close()
        raise ProviderError('artifact_unavailable')
    etag = f'"{result["sha256"]}"'
    headers = {'ETag': etag, 'Accept-Ranges': 'bytes', 'Content-Length': str(size),
               'Content-Disposition': f'inline; filename="museforge-{identifier}.wav"'}
    if request.method == 'HEAD':
        file.close()
        return Response(media_type=result['media_type'], headers=headers)
    first, last, status = 0, size-1, 200
    requested = request.headers.get('range')
    if requested and request.headers.get('if-range', etag) == etag:
        try: first, last = range_bounds(requested, size)
        except ValueError:
            file.close()
            return Response(status_code=416, headers={'Content-Range': f'bytes */{size}', 'ETag': etag})
        status = 206
        headers.update({'Content-Range': f'bytes {first}-{last}/{size}', 'Content-Length': str(last-first+1)})
    def chunks():
        try:
            file.seek(first)
            remaining = last-first+1
            while remaining:
                data = file.read(min(65536, remaining))
                if not data: break
                remaining -= len(data)
                yield data
        finally: file.close()
    return StreamingResponse(chunks(), status_code=status, media_type=result['media_type'], headers=headers,
                             background=BackgroundTask(file.close))
