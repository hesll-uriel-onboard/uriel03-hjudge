from os import environ

from sqlalchemy import create_engine
from sqlalchemy.orm import registry

def _db_url() -> str:
    url = environ.get("DATABASE_URL")
    if url:
        return url.replace("postgres://", "postgresql://", 1)
    user = environ.get("DB_USER")
    password = environ.get("DB_PASS")
    host = environ.get("DB_HOST")
    name = environ.get("DB_NAME")
    return f"postgresql://{user}:{password}@{host}/{name}"

DEFAULT_CONNECTION_STRING = _db_url()
DEFAULT_ENGINE = create_engine(DEFAULT_CONNECTION_STRING)

# mapper between tables and entities
mapper_registry = registry()
