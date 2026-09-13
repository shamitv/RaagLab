from sqlalchemy import create_engine
from museforge.config import Settings


def engine_for(settings: Settings):
    return create_engine(settings.database_url.get_secret_value(), pool_pre_ping=True,
                         connect_args={"connect_timeout": 3, "options": "-c statement_timeout=5000"})
