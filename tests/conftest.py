"""Create an empty database and migrate all"""

import os
import pathlib
from typing import Generator

import pytest
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import RevisionStep
from alembic.script import ScriptDirectory
from litestar import Litestar
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from hjudge.app import provide_app
from hjudge.commons.db.uow import (
    AbstractUnitOfWork,
    SQLAlchemyUnitOfWork,
)
from hjudge.oj.models.judges.factory import DEFAULT_JUDGE_FACTORY

CURRENT_DIRECTORY = pathlib.Path(__file__).parent
NAME = ".db"
DATABASE_FILENAME = f"{CURRENT_DIRECTORY}/{NAME}"

# remove database
if os.path.exists(DATABASE_FILENAME):
    os.remove(DATABASE_FILENAME)
with open(DATABASE_FILENAME, "w") as f:
    f.write("")

# create file if not exists before
SQLITE_CONNECTION_STRING = f"sqlite:///{DATABASE_FILENAME}"
DEFAULT_ENGINE = create_engine(SQLITE_CONNECTION_STRING, echo=True)


def run_migrations() -> None:
    """Run migrations"""

    def my_function(
        rev: str, context: EnvironmentContext
    ) -> list[RevisionStep]:
        head: str | None = script.get_current_head()
        if head is not None:
            return script._upgrade_revs(head, rev)
        assert False

    config = Config(file_=f"{CURRENT_DIRECTORY.parent}/alembic.ini")
    config.set_main_option("sqlalchemy.url", SQLITE_CONNECTION_STRING)

    script = ScriptDirectory.from_config(config)
    context = EnvironmentContext(config=config, script=script, fn=my_function)
    with DEFAULT_ENGINE.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


run_migrations()


@pytest.fixture(scope="session")
def engine() -> Engine:
    return create_engine(SQLITE_CONNECTION_STRING)


@pytest.fixture(scope="session")
def uow(engine: Engine) -> Generator[AbstractUnitOfWork, None, None]:
    yield SQLAlchemyUnitOfWork(sessionmaker(bind=engine))
    engine.dispose()


@pytest.fixture(scope="session")
def app(uow: AbstractUnitOfWork) -> Litestar:
    app = provide_app(uow, DEFAULT_JUDGE_FACTORY)
    app.debug = True
    return app
