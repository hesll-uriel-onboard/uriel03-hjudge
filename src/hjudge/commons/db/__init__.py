from sqlalchemy import create_engine
from sqlalchemy.orm import registry

# engine
DEFAULT_CONNECTION_STRING = "postgresql://postgres:example@localhost/hjudge"
DEFAULT_ENGINE = create_engine(DEFAULT_CONNECTION_STRING)

# mapper between tables and entities
mapper_registry = registry()
