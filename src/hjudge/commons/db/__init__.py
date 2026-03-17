from os import environ

from sqlalchemy import create_engine
from sqlalchemy.orm import registry

DB_USER = environ.get("DB_USER")
DB_PASS = environ.get("DB_PASS")
DB_HOST = environ.get("DB_HOST")
DB_NAME = environ.get("DB_NAME")
DEFAULT_CONNECTION_STRING = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
)
DEFAULT_ENGINE = create_engine(DEFAULT_CONNECTION_STRING)

# mapper between tables and entities
mapper_registry = registry()
