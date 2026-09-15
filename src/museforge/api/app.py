import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from museforge.domain import ProviderError
from museforge.api.routes import router, readiness as provider_readiness
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from museforge.config import Settings
from museforge.db.connection import engine_for
from museforge.observability import check_schema


class Liveness(BaseModel):
    status: Literal["alive"] = "alive"


class Readiness(BaseModel):
    status: Literal["ready", "unavailable"]
    dependencies: dict[str, str]
    services: dict[str, str]
    generation: Literal["ready", "unavailable"] = "unavailable"


def storage_readiness(settings, engine):
    dependencies = {"database": "unavailable", "schema": "unavailable", "artifacts": "unavailable"}
    services = {"dispatcher": "unobserved", settings.worker_role: "unobserved", "broker": "unobserved", "provider": "offline"}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            dependencies["database"] = "ready"
            check_schema(connection, settings)
            dependencies["schema"] = "ready"
            observations = connection.execute(text("""
                SELECT role, bool_or(broker_connected) AS broker_connected
                FROM process_heartbeats WHERE expires_at > now() GROUP BY role
            """)).mappings().all()
            for row in observations:
                observed_role = settings.worker_role if row["role"] == "worker-mock" else row["role"]
                services[observed_role] = "ready" if row["broker_connected"] else "degraded"
            services["provider"] = provider_readiness(connection, settings)["state"]
            if observations:
                services["broker"] = "observed_connected" if any(row["broker_connected"] for row in observations) else "degraded"
    except Exception:
        pass  # Dependency detail intentionally excludes credentials, SQL and server text.
    try:
        root = settings.artifact_root
        if root.is_dir() and not root.is_symlink() and os.access(root, os.R_OK | os.X_OK):
            with os.scandir(root) as entries:
                next(entries, None)
            dependencies["artifacts"] = "ready"
    except OSError:
        pass
    return Readiness(status="ready" if all(v == "ready" for v in dependencies.values()) else "unavailable",
                     dependencies=dependencies, services=services, generation="ready" if services["provider"] in ("ready", "busy") else "unavailable")


def is_client_route(path: str):
    if path in {"", "create", "projects", "library", "songs", "settings", "templates"}:
        return True
    if path.startswith("projects/"):
        try:
            return str(UUID(path[9:])) == path[9:].lower()
        except ValueError:
            return False
    if path.startswith("songs/"):
        try:
            return str(UUID(path[6:])) == path[6:].lower()
        except ValueError:
            return False
    return False


def create_app(settings: Settings | None = None):
    settings = settings or Settings()
    engine = engine_for(settings)

    @asynccontextmanager
    async def lifespan(app):
        yield
        engine.dispose()

    app = FastAPI(title="MuseForge AI", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine

    def error(code, status, correlation, fields=None):
        return JSONResponse({'code': code, 'message': code.replace('_', ' '),
            'retryable': status == 503, 'correlation_id': correlation, 'fields': fields}, status_code=status)

    @app.middleware('http')
    async def bounded_body(request: Request, call_next):
        request.state.correlation_id = str(uuid4())
        if request.method in ('POST', 'PATCH', 'PUT'):
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 131072:
                    return error('request_too_large', 413, request.state.correlation_id)
            request._body = bytes(body)
        response = await call_next(request)
        response.headers['X-Correlation-ID'] = request.state.correlation_id
        if request.url.path.startswith('/api/v1') and not request.url.path.startswith('/api/v1/artifacts/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        return error('not_found' if exc.status_code == 404 else 'request_failed', exc.status_code, request.state.correlation_id)

    @app.exception_handler(ProviderError)
    async def provider_error(request, exc):
        status = {'not_found': 404, 'idempotency_conflict': 409, 'project_archived': 409,
                  'active_jobs_conflict': 409, 'retry_not_allowed': 409,
                  'revision_required': 428, 'revision_conflict': 412, 'artifact_unavailable': 410, 'invalid_cursor': 422}.get(exc.code, 422)
        return error(exc.code, status, request.state.correlation_id)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        fields = [{'field': '.'.join(str(v) for v in item['loc']), 'code': item['type']} for item in exc.errors()]
        return error('invalid_request', 422, request.state.correlation_id, fields)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        return error('storage_unavailable', 503, request.state.correlation_id)

    app.include_router(router)

    @app.get("/health/live", response_model=Liveness)
    def live():
        return Liveness()

    @app.get("/health/ready", response_model=Readiness, responses={503: {"model": Readiness}})
    def ready():
        result = storage_readiness(settings, app.state.engine)
        return JSONResponse(result.model_dump(), status_code=200 if result.status == "ready" else 503,
                            headers={"Cache-Control": "no-store"})

    @app.get("/assets/{path:path}", include_in_schema=False)
    def assets(path: str):
        root = settings.web_dist / "assets"
        candidate = root / path
        # Only emitted asset files, never dotfiles, symlinks or traversal.
        if any(part.startswith(".") for part in Path(path).parts):
            raise HTTPException(404, "Asset not found")
        try:
            resolved = candidate.resolve(strict=True)
            if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
                raise ValueError
            current = candidate
            while current != root:
                if current.is_symlink():
                    raise ValueError
                current = current.parent
        except (OSError, ValueError, RuntimeError):
            raise HTTPException(404, "Asset not found") from None
        immutable = bool(re.search(r"-[A-Za-z0-9_-]{8,}\.[^.]+$", resolved.name))
        return FileResponse(resolved, headers={"Cache-Control": "public, max-age=31536000, immutable" if immutable else "no-cache"})

    @app.get("/{path:path}", include_in_schema=False)
    def shell(path: str):
        if not is_client_route(path):
            raise HTTPException(404, "Not found")
        index = settings.web_dist / "index.html"
        if not index.is_file():
            raise HTTPException(503, "Frontend build unavailable")
        return FileResponse(index, media_type="text/html", headers={"Cache-Control": "no-cache"})

    return app
