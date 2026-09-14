from contextlib import contextmanager
from unittest.mock import Mock
from museforge.api.app import storage_readiness
from museforge.config import Settings


class Engine:
    def __init__(self, settings, head='0003_workspace_settings', workspace=True):
        self.settings, self.head, self.workspace = settings, head, workspace

    @contextmanager
    def connect(self):
        yield self

    def execute(self, statement):
        result = Mock()
        result.scalars.return_value.all.return_value = [self.head]
        result.mappings.return_value.all.return_value = []
        return result

    def scalar(self, *args):
        return self.settings.workspace_id if self.workspace else None


def test_missing_workers_do_not_block_storage(tmp_path):
    settings = Settings(_env_file=None, artifact_root=tmp_path)
    health = storage_readiness(settings, Engine(settings))
    assert health.status == 'ready'
    assert health.services['worker-mock'] == 'unobserved'
    assert health.generation == 'unavailable'


def test_old_schema_and_missing_workspace_block_readiness(tmp_path):
    settings = Settings(_env_file=None, artifact_root=tmp_path)
    for engine in (Engine(settings, head='old'), Engine(settings, workspace=False)):
        health = storage_readiness(settings, engine)
        assert health.status == 'unavailable'
        assert health.dependencies['database'] == 'ready'
        assert health.dependencies['schema'] == 'unavailable'


def test_missing_or_symlinked_storage_blocks_readiness(tmp_path):
    for path in (tmp_path / 'missing', tmp_path / 'link'):
        if path.name == 'link':
            path.symlink_to(tmp_path, target_is_directory=True)
        settings = Settings(_env_file=None, artifact_root=path)
        assert storage_readiness(settings, Engine(settings)).dependencies['artifacts'] == 'unavailable'
