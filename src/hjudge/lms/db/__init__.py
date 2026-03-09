from sqlalchemy import create_engine

# TODO: create
DEFAULT_CONNECTION_STRING = "postgresql://postgres:example@localhost/hjudge"
DEFAULT_ENGINE = create_engine(DEFAULT_CONNECTION_STRING)
