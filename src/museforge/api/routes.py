"""Workspace-scoped public generation and media endpoints."""
import base64
import os
import json
import hashlib
from datetime import datetime
from uuid import UUID
import sqlalchemy as sa
from fastapi import APIRouter, Header, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.background import BackgroundTask
from museforge.db import schema as db
from museforge.domain import Accepted, Generation, ProjectCreate, ProjectPatch, VersionPatch, Iteration, ProviderError, provider_capabilities
from museforge.domain import ErrorResponse, CapabilitiesResponse, ProjectView, ProjectDetail, ProjectPage, JobView, VersionPage, VersionDetail
from museforge.domain import FrontendConfig, LibraryPage, SettingsPatch, SettingsView, TemplatePage, TemplateView
from museforge.jobs import accepted, cancel, retry as retry_job, row, scoped, submit
from museforge.projects import duplicate, set_archived
from museforge.workspace import DEFAULT_GENERATION_DEFAULTS, TEMPLATES, ensure_settings, settings_view, updated_at
from museforge.storage import open_artifact, range_bounds

router = APIRouter(prefix='/api/v1', responses={status: {'model': ErrorResponse}
    for status in (404, 409, 410, 412, 413, 422, 428, 503)})


def context(request): return request.app.state.engine, request.app.state.settings


def page(c, table, settings, limit, cursor, *conditions, descending=False, filter_context=''):
    query = sa.select(table).where(scoped(table, settings), *conditions)
    if cursor:
        try:
            raw = json.loads(base64.urlsafe_b64decode(cursor.encode() + b'=' * (-len(cursor) % 4)))
            if len(raw) == 3:
                stamp, identifier, context = raw
                if context != hashlib.sha256(filter_context.encode()).hexdigest(): raise ValueError
            elif len(raw) == 2 and not filter_context:
                stamp, identifier = raw
            else:
                raise ValueError
            cursor_value = sa.tuple_(datetime.fromisoformat(stamp), UUID(identifier))
            current_value = sa.tuple_(table.c.created_at, table.c.id)
            query = query.where(current_value < cursor_value if descending else current_value > cursor_value)
        except Exception: raise ProviderError('invalid_cursor') from None
    order = (table.c.created_at.desc(), table.c.id.desc()) if descending else (table.c.created_at, table.c.id)
    rows = [dict(r) for r in c.execute(query.order_by(*order).limit(limit + 1)).mappings()]
    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = base64.urlsafe_b64encode(json.dumps([
            last['created_at'].isoformat(), str(last['id']),
            hashlib.sha256(filter_context.encode()).hexdigest(),
        ]).encode()).decode()
    return dict(items=rows[:limit], next_cursor=next_cursor)


def escaped_like(value):
    return '%' + value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'


def library_page(c, settings, limit, cursor, q, favorite_only, genre, language, sort):
    favorite = sa.exists(sa.select(1).select_from(db.favorites).where(
        db.favorites.c.version_id == db.versions.c.id,
        scoped(db.favorites, settings),
    ))
    statement = sa.select(
        db.versions.c.project_id,
        db.projects.c.title.label('project_title'),
        db.versions.c.id.label('version_id'),
        db.versions.c.number.label('version_number'),
        db.versions.c.label.label('version_label'),
        favorite.label('favorite'),
        db.versions.c.created_at,
        db.versions.c.inputs['genre'].astext.label('genre'),
        db.versions.c.inputs['language'].astext.label('language'),
        db.artifacts.c.duration_seconds,
        db.artifacts.c.available_at,
    ).select_from(db.versions).join(
        db.projects, sa.and_(db.projects.c.id == db.versions.c.project_id,
                             db.projects.c.workspace_id == db.versions.c.workspace_id)
    ).outerjoin(
        db.links, sa.and_(db.links.c.version_id == db.versions.c.id, db.links.c.role == 'audio')
    ).outerjoin(
        db.artifacts, sa.and_(db.artifacts.c.id == db.links.c.artifact_id,
                              db.artifacts.c.workspace_id == settings.workspace_id)
    ).where(
        db.versions.c.workspace_id == settings.workspace_id,
        db.projects.c.archived_at.is_(None),
    )
    if q:
        pattern = escaped_like(q)
        statement = statement.where(sa.or_(db.projects.c.title.ilike(pattern, escape='\\'),
                                           db.versions.c.label.ilike(pattern, escape='\\')))
    if favorite_only:
        statement = statement.where(favorite)
    if genre:
        statement = statement.where(db.versions.c.inputs['genre'].astext == genre)
    if language:
        statement = statement.where(db.versions.c.inputs['language'].astext == language)
    filter_context = json.dumps([q, favorite_only, genre, language, sort], ensure_ascii=False, separators=(',', ':'))
    if cursor:
        try:
            raw = json.loads(base64.urlsafe_b64decode(cursor.encode() + b'=' * (-len(cursor) % 4)))
            if len(raw) != 3 or raw[2] != hashlib.sha256(filter_context.encode()).hexdigest(): raise ValueError
            stamp, identifier = datetime.fromisoformat(raw[0]), UUID(raw[1])
            cursor_value = sa.tuple_(stamp, identifier)
            current_value = sa.tuple_(db.versions.c.created_at, db.versions.c.id)
            statement = statement.where(current_value < cursor_value if sort == 'recent' else current_value > cursor_value)
        except Exception: raise ProviderError('invalid_cursor') from None
    ordering = (db.versions.c.created_at.desc(), db.versions.c.id.desc()) if sort == 'recent' else (db.versions.c.created_at, db.versions.c.id)
    rows = [dict(item) for item in c.execute(statement.order_by(*ordering).limit(limit + 1)).mappings()]
    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = base64.urlsafe_b64encode(json.dumps([
            last['created_at'].isoformat(), str(last['version_id']),
            hashlib.sha256(filter_context.encode()).hexdigest(),
        ]).encode()).decode()
    items = [{key: value for key, value in item.items() if key != 'available_at'} | {
        'available': item['available_at'] is not None,
    } for item in rows[:limit]]
    return {'items': items, 'next_cursor': next_cursor}


def job_detail(c, settings, identifier):
    job = row(c, db.jobs, identifier, settings)
    result = {k: job[k] for k in ('id', 'project_id', 'operation', 'retry_of_job_id', 'state', 'stage', 'progress', 'attempt_count', 'cancellation_requested_at',
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
    rows = c.execute(sa.select(db.registrations.c.readiness, db.registrations.c.last_heartbeat,
        db.registrations.c.runtime_metadata).where(
        scoped(db.registrations, settings), db.registrations.c.provider_route == settings.provider_route,
        db.registrations.c.provider_id == settings.provider_id,
        db.registrations.c.provider_revision == settings.provider_revision,
        db.registrations.c.model_id == settings.model_id,
        db.registrations.c.model_revision == settings.model_revision,
        db.registrations.c.capability_revision == settings.provider_revision,
        db.registrations.c.expires_at > sa.func.now()).order_by(db.registrations.c.last_heartbeat.desc())).mappings().all()
    selected = next((r for r in rows if r['readiness'] == 'busy'), rows[0] if rows else None)
    runtime = selected['runtime_metadata'] if selected else {}
    return dict(state=selected['readiness'] if selected else 'offline',
                last_observed_at=selected['last_heartbeat'] if selected else None,
                device=runtime.get('device'), fallback_reason=runtime.get('fallback_reason'))


@router.get('/capabilities', response_model=CapabilitiesResponse)
def get_capabilities(request: Request):
    engine, settings = context(request)
    with engine.connect() as c:
        return dict(provider_capabilities(settings) | {'duration': {'min': 5, 'max': 30, 'default': settings.duration_seconds}}, default_lyrics_mode=settings.lyrics_provider,
                    readiness=readiness(c, settings))


@router.get('/frontend-config', response_model=FrontendConfig)
def frontend_config(request: Request):
    value = request.app.state.settings.song_link_base_url
    return {'song_link_base_url': str(value).rstrip('/') if value else None}


@router.get('/settings', response_model=SettingsView)
def get_settings(request: Request, response: Response):
    engine, settings = context(request)
    with engine.begin() as c:
        record = ensure_settings(c, settings)
    response.headers['ETag'] = f'"{record["revision"]}"'
    return settings_view(record)


@router.patch('/settings', response_model=SettingsView)
def patch_settings(body: SettingsPatch, request: Request, response: Response,
                   if_match: str | None = Header(None)):
    engine, settings = context(request)
    with engine.begin() as c:
        ensure_settings(c, settings)
        current = c.execute(sa.select(db.workspace_settings).where(
            db.workspace_settings.c.workspace_id == settings.workspace_id
        ).with_for_update()).mappings().one()
        require_revision(if_match, current)
        values = body.model_dump(mode='json', exclude_unset=True)
        values.update(revision=current['revision'] + 1, updated_at=sa.func.now())
        record = c.execute(db.workspace_settings.update().where(
            db.workspace_settings.c.workspace_id == settings.workspace_id
        ).values(**values).returning(db.workspace_settings)).mappings().one()
    response.headers['ETag'] = f'"{record["revision"]}"'
    return settings_view(record)


@router.get('/templates', response_model=TemplatePage)
def templates():
    return {'items': TEMPLATES}


@router.get('/templates/{template_id}', response_model=TemplateView)
def template(template_id: str):
    selected = next((item for item in TEMPLATES if item['id'] == template_id), None)
    if selected is None: raise ProviderError('not_found')
    return selected


@router.get('/library', response_model=LibraryPage)
def library(request: Request, q: str | None = Query(None, max_length=120),
            favorite_only: bool = False, genre: str | None = None, language: str | None = None,
            sort: str = Query('recent', pattern='^(recent|oldest)$'),
            limit: int = Query(20, ge=1, le=100), cursor: str | None = None):
    engine, settings = context(request)
    if genre is not None and genre not in ('Indie Pop', 'Pop', 'Folk', 'Ambient', 'Rock', 'Electronic'):
        raise ProviderError('invalid_request')
    if language is not None and language not in ('Hindi', 'English', 'Hinglish', 'Punjabi', 'Tamil'):
        raise ProviderError('invalid_request')
    with engine.connect() as c:
        return library_page(c, settings, limit, cursor, q, favorite_only, genre, language, sort)


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
def projects(request: Request, q: str | None = Query(None, max_length=120),
             archived: str = Query('active', pattern='^(active|archived|all)$'),
             limit: int = Query(20, ge=1, le=100), cursor: str | None = None):
    engine, settings = context(request)
    conditions = []
    if archived == 'active': conditions.append(db.projects.c.archived_at.is_(None))
    elif archived == 'archived': conditions.append(db.projects.c.archived_at.is_not(None))
    if q: conditions.append(db.projects.c.title.ilike(escaped_like(q), escape='\\'))
    filter_context = json.dumps([q, archived], ensure_ascii=False, separators=(',', ':'))
    with engine.connect() as c:
        return page(c, db.projects, settings, limit, cursor, *conditions, descending=True, filter_context=filter_context)


@router.post('/projects/{identifier}/duplicate', status_code=201, response_model=ProjectView)
def duplicate_project(identifier: UUID, request: Request, response: Response):
    engine, settings = context(request)
    result = duplicate(engine, settings, identifier)
    response.headers['Location'] = f"/api/v1/projects/{result['id']}"
    response.headers['ETag'] = f'"{result["revision"]}"'
    return result


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


@router.post('/jobs/{identifier}/retry', status_code=202, response_model=Accepted)
def retry_generation(identifier: UUID, request: Request, response: Response,
                     idempotency_key: str = Header(min_length=16, max_length=128)):
    engine, settings = context(request)
    result = retry_job(engine, settings, identifier, idempotency_key)
    response.headers['Location'] = result['status_url']
    return result


@router.get('/projects/{identifier}/versions', response_model=VersionPage)
def versions(identifier: UUID, request: Request, limit: int = Query(20, ge=1, le=100), cursor: str | None = None):
    engine, settings = context(request)
    with engine.connect() as c:
        row(c, db.projects, identifier, settings)
        result = page(c, db.versions, settings, limit, cursor, db.versions.c.project_id == identifier)
        favorites = set(c.execute(sa.select(db.favorites.c.version_id).where(scoped(db.favorites, settings),
            db.favorites.c.version_id.in_([v['id'] for v in result['items']]))).scalars())
        for item in result['items']: item['favorite'] = item['id'] in favorites
        return result


@router.get('/versions/{identifier}', response_model=VersionDetail)
def version(identifier: UUID, request: Request, response: Response):
    engine, settings = context(request)
    with engine.connect() as c:
        result = row(c, db.versions, identifier, settings)
        response.headers['ETag'] = f'"{result["revision"]}"'
        result['favorite'] = c.scalar(sa.select(sa.exists().where(db.favorites.c.version_id == identifier, scoped(db.favorites, settings))))
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
    try:
        file = open_artifact(settings.artifact_root, result['storage_key'])
    except ProviderError:
        with engine.begin() as c:
            c.execute(db.artifacts.update().where(
                db.artifacts.c.id == identifier,
                db.artifacts.c.workspace_id == settings.workspace_id,
            ).values(available_at=None))
        raise
    size = os.fstat(file.fileno()).st_size
    if size != result['byte_size']:
        file.close()
        with engine.begin() as c:
            c.execute(db.artifacts.update().where(
                db.artifacts.c.id == identifier,
                db.artifacts.c.workspace_id == settings.workspace_id,
            ).values(available_at=None))
        raise ProviderError('artifact_unavailable')
    if result['available_at'] is None:
        with engine.begin() as c:
            c.execute(db.artifacts.update().where(
                db.artifacts.c.id == identifier,
                db.artifacts.c.workspace_id == settings.workspace_id,
            ).values(available_at=sa.func.now()))
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


def require_revision(value, record):
    if value is None: raise ProviderError('revision_required')
    if value != f'"{record["revision"]}"': raise ProviderError('revision_conflict')


@router.patch('/projects/{identifier}', response_model=ProjectView)
def patch_project(identifier: UUID, body: ProjectPatch, request: Request, response: Response,
                  if_match: str | None = Header(None)):
    engine, settings = context(request)
    with engine.begin() as c:
        current = row(c, db.projects, identifier, settings, True)
        require_revision(if_match, current)
        values = body.model_dump(mode='python', exclude_unset=True)
        if body.draft: values['draft'] = body.draft.model_dump(mode='json')
        if 'archived' in values:
            archived = values.pop('archived')
            if archived != (current['archived_at'] is not None):
                values['archived_at'] = set_archived(c, current, archived)
        if 'active_version_id' in values:
            if body.active_version_id:
                selected = row(c, db.versions, body.active_version_id, settings)
                if selected['project_id'] != identifier: raise ProviderError('invalid_request')
            values['selection_epoch'] = current['selection_epoch'] + 1
        values['revision'] = current['revision'] + 1
        result = dict(c.execute(db.projects.update().where(db.projects.c.id == identifier).values(**values).returning(db.projects)).mappings().one())
    response.headers['ETag'] = f'"{result["revision"]}"'
    return result


@router.patch('/versions/{identifier}', response_model=VersionDetail)
def patch_version(identifier: UUID, body: VersionPatch, request: Request, response: Response,
                  if_match: str | None = Header(None)):
    engine, settings = context(request)
    with engine.begin() as c:
        current = row(c, db.versions, identifier, settings, True)
        require_revision(if_match, current)
        values = {'revision': current['revision'] + 1}
        if body.label is not None: values['label'] = body.label
        if body.favorite is not None:
            c.execute(db.favorites.delete().where(db.favorites.c.version_id == identifier, scoped(db.favorites, settings)))
            if body.favorite: c.execute(db.favorites.insert().values(workspace_id=settings.workspace_id, version_id=identifier))
        c.execute(db.versions.update().where(db.versions.c.id == identifier).values(**values))
    return version(identifier, request, response)


@router.post('/versions/{identifier}/iterations', status_code=202, response_model=Accepted)
def iteration(identifier: UUID, body: Iteration, request: Request, response: Response,
              idempotency_key: str = Header(min_length=16, max_length=128)):
    engine, settings = context(request)
    with engine.connect() as c: source = row(c, db.versions, identifier, settings)
    inputs = body.inputs.model_copy(update={'project_id': source['project_id']})
    result = submit(engine, settings, inputs, idempotency_key, body.operation, identifier)
    response.headers['Location'] = result['status_url']
    return result
