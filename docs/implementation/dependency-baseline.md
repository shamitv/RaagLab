# Dependency and image baseline

- Checked: 2026-09-13
- State: selected planning pins; temporary resolution checks completed, application manifests/locks and container builds pending Phase 01

## Selected direct dependencies

Select these exact versions in Phase 01 manifests. Freeze every transitive dependency with `uv.lock` and `apps/web/package-lock.json`, install frozen in images/CI, and record any justified change here and in the phase status. Do not copy `latest` tags into Dockerfiles.

| Runtime / package | Selected pin | Evidence |
| --- | --- | --- |
| Python | 3.13.15 | Official image tag below; [Python support status](https://devguide.python.org/versions/) lists 3.13 as supported |
| uv | 0.12.13 | [PyPI metadata](https://pypi.org/pypi/uv/0.12.13/json) |
| FastAPI | 0.141.1 | [PyPI metadata](https://pypi.org/pypi/fastapi/0.141.1/json) |
| Pydantic / pydantic-settings | 2.13.5 / 2.15.0 | [Pydantic metadata](https://pypi.org/pypi/pydantic/2.13.5/json), [settings metadata](https://pypi.org/pypi/pydantic-settings/2.15.0/json) |
| SQLAlchemy / Alembic | 2.0.52 / 1.20.0 | [SQLAlchemy metadata](https://pypi.org/pypi/SQLAlchemy/2.0.52/json), [Alembic metadata](https://pypi.org/pypi/alembic/1.20.0/json) |
| psycopg[binary] | 3.3.5 | [PyPI metadata](https://pypi.org/pypi/psycopg/3.3.5/json) |
| Celery | 5.6.3 | [PyPI metadata](https://pypi.org/pypi/celery/5.6.3/json) |
| Uvicorn | 0.52.4 | [PyPI metadata](https://pypi.org/pypi/uvicorn/0.52.4/json) |
| pytest / HTTPX | 9.1.1 / 0.28.1 | [pytest metadata](https://pypi.org/pypi/pytest/9.1.1/json), [HTTPX metadata](https://pypi.org/pypi/httpx/0.28.1/json) |
| PostgreSQL | 18.6 | [Supported version table](https://www.postgresql.org/support/versioning/) |
| RabbitMQ | 4.3.5 | [Release/support information](https://www.rabbitmq.com/release-information); recheck before 2026-11-30 community-support end |
| Node.js / npm | 24.21.0 / 11.19.0 | [Official release index](https://nodejs.org/dist/index.json), Node 24 LTS release dated 2026-09-07 |
| React / React DOM | 19.3.0 / 19.3.0 | [React](https://registry.npmjs.org/react/19.3.0), [React DOM](https://registry.npmjs.org/react-dom/19.3.0) registry metadata |
| React Router DOM | 7.18.3 | [Registry metadata](https://registry.npmjs.org/react-router-dom/7.18.3) |
| TypeScript | 5.9.3 | [Registry metadata](https://registry.npmjs.org/typescript/5.9.3); compatible with OpenAPI type generator peer requirement |
| Vite / React plugin | 8.3.0 / 6.1.1 | [Vite](https://registry.npmjs.org/vite/8.3.0), [plugin](https://registry.npmjs.org/@vitejs/plugin-react/6.1.1) metadata |
| @types/react / @types/react-dom | 19.3.0 / 19.3.0 | [React types](https://registry.npmjs.org/@types/react/19.3.0), [DOM types](https://registry.npmjs.org/@types/react-dom/19.3.0) |
| openapi-typescript | 7.13.0 | [Registry metadata](https://registry.npmjs.org/openapi-typescript/7.13.0); peer TypeScript `^5.x` |
| @playwright/test / @axe-core/playwright | 1.63.0 / 4.13.0 | [Playwright](https://registry.npmjs.org/@playwright/test/1.63.0), [axe integration](https://registry.npmjs.org/@axe-core/playwright/4.13.0) |
| Vitest | 5.0.0 | [Registry metadata](https://registry.npmjs.org/vitest/5.0.0); supports selected Vite 8 and Node 24 |

Vite requires a supported modern Node runtime; Node 24 meets the published [Vite requirements](https://vite.dev/guide/) and the selected toolchain's engine constraints. TypeScript 7.0.2 was observed as the registry latest but was not selected because the OpenAPI generator currently declares TypeScript 5 support. Optional React compiler/Babel peers are not needed for the initial SPA.

## Image pins observed from official-image registry metadata

Use these tags with the recorded digest in the corresponding `FROM` or Compose image selection. Phase 01 must validate architecture availability and pull/build the intended images. Registry metadata is not execution evidence.

| Role | Tag | Manifest digest |
| --- | --- | --- |
| API and mock Python base | `python:3.13.15-slim-bookworm` | `sha256:ed86c82274b3c69b52fb5820f358f0bd7df0b603332063cb5c6e32bd220c3e6e` |
| Frontend build | `node:24.21.0-bookworm-slim` | `sha256:2fe369e969550cde8e867afc3fe370b260140cab4a23d467074295b42163d553` |
| Database | `postgres:18.6-bookworm` | `sha256:1c59e2c3c818eaa0f0628f695b36e7c9e362d6b219b36a54a32df645cbd7e1af` |
| Broker | `rabbitmq:4.3.5` | `sha256:078107e036374f4d9bbeab8766799abe474bf252aedb4617ddd2edfa8e2c2c05` |

Sources: official Docker Hub tag APIs for [Python](https://hub.docker.com/v2/repositories/library/python/tags/3.13.15-slim-bookworm), [Node](https://hub.docker.com/v2/repositories/library/node/tags/24.21.0-bookworm-slim), [PostgreSQL](https://hub.docker.com/v2/repositories/library/postgres/tags/18.6-bookworm), and [RabbitMQ](https://hub.docker.com/v2/repositories/library/rabbitmq/tags/4.3.5). Pinning is a reproducibility baseline; assess relevant fixes at build/release time and deliberately refresh digests with recorded verification.

Docker Engine is a host prerequisite, not an application-bundled dependency. Require the Compose v2 plugin, minimum 2.24.4 for the planned features, then record the exact installed engine/Compose versions when tested in Phase 01 and Part 2. The plan does not install or claim a particular host engine. Node exists only in build/test/development; API and CPU mock dependency groups exclude Torch, Transformers, CUDA and model weights. A later real-worker group has its own compatible lock/runtime chosen with the model.

## Compatibility checks actually performed

Read registry `requires_python`, dependency constraints, npm engines/peers and official runtime/support documents. Python 3.13 meets the selected direct packages' requirements. A temporary pip dry run resolved the ten application/test Python pins for CPython 3.13 Linux x86_64 wheel targets. Important resolved versions included Starlette 1.6.0, Kombu 5.6.2, billiard 4.2.4 and pydantic-core 2.46.5. These remain subject to the real frozen-lock build and runtime integration tests.

A temporary `npm install --package-lock-only --ignore-scripts --no-audit --no-fund` resolved the frontend pins. It warned that the authoring Node 25.2.1 is outside Vitest 5's engine range; the selected container Node 24.21.0 is in range. No frontend package scripts or browser tests ran. The pip command first encountered a local virtualenv-required setting; it was rerun successfully inside an isolated temporary virtual environment. No application dependency was installed into the repository or global environment.

See [planning verification](evidence/planning-verification.md) for commands, results and limitations. These checks prove resolvability and declared compatibility, not that the application builds, starts, or works. Phase 01 must generate actual manifests and transitive locks, verify frozen installs, run migrations against PostgreSQL, build images and perform the service/static-hosting checks. Phase 06 rechecks version support and any required update evidence before release.
