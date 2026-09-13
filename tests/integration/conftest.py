import os
import pytest
from museforge.config import Settings
from museforge.db.connection import engine_for


def pytest_collection_modifyitems(items):
    if os.environ.get('FOUNDATION_INTEGRATION') != '1':
        raise pytest.UsageError('Integration requires the isolated stack: bash scripts/test.sh integration')
    for item in items:
        item.add_marker(pytest.mark.integration)


@pytest.fixture(scope='session')
def settings():
    return Settings()


@pytest.fixture(scope='session')
def engine(settings):
    engine = engine_for(settings)
    yield engine
    engine.dispose()
