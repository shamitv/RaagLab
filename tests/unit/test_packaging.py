import ast
import importlib.util
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from museforge.db.schema import metadata

ROOT = Path(__file__).resolve().parents[2]


def test_api_does_not_import_worker_or_inference():
    for path in (ROOT / 'src/museforge/api').glob('*.py'):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ''
                assert not module.startswith(('celery', 'torch', 'transformers', 'museforge.worker', 'museforge.dispatcher'))


def test_frozen_initial_schema_matches_models():
    spec = importlib.util.spec_from_file_location('initial_schema', ROOT / 'migrations/versions/0001_foundation.py')
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    dialect = postgresql.dialect()
    assert set(metadata.tables) - set(migration.metadata.tables) == {
        "version_favorites",
        "workspace_settings",
    }
    for name in migration.metadata.tables:
        table = metadata.tables[name]
        assert str(sa.schema.CreateTable(table).compile(dialect=dialect)) == str(sa.schema.CreateTable(migration.metadata.tables[name]).compile(dialect=dialect))


def test_build_and_ignore_boundaries():
    dockerfile = (ROOT / 'packaging/Dockerfile').read_text()
    assert 'npm ci' in dockerfile and 'uv sync --frozen' in dockerfile
    for line in dockerfile.splitlines():
        if line.startswith('FROM ') and ' AS ' in line and ':' in line:
            assert '@sha256:' in line
    assert 'COPY --from=web-build /web/dist /app/web' in dockerfile
    for name in ('.gitignore', '.dockerignore'):
        content = (ROOT / name).read_text()
        for excluded in ('.env', 'weights', 'artifacts', 'node_modules', '*.safetensors'):
            assert excluded in content
    assert '--volumes' not in (ROOT / 'scripts/stop.sh').read_text()


def test_yue2_worker_isolated_and_hash_locked():
    dockerfile = (ROOT / 'packaging/yue2/Dockerfile.worker').read_text()
    lock = (ROOT / 'packaging/yue2/requirements.museforge.lock').read_text()
    compose = (ROOT / 'compose.yue2.yaml').read_text()
    assert '--require-hashes' in dockerfile
    assert 'requirements.museforge.lock' in dockerfile
    assert 'museforge.yue2.v1' in compose and 'yue2_weights:/weights:ro' in compose
    assert lock.count('==') == lock.count('--hash=sha256:')
    assert 'torch' not in (ROOT / 'pyproject.toml').read_text()
    assert 'transformers' not in (ROOT / 'pyproject.toml').read_text()
