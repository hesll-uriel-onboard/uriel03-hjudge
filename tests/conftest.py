"""Create an empty database and migrate all"""

import json
import os
import pathlib
import re
from typing import Generator
from unittest.mock import MagicMock

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
    SQLAlchemyUOWFactory,
)
from hjudge.oj.models.judges import AbstractCrawler
from hjudge.oj.models.judges.factory import DEFAULT_JUDGE_FACTORY, JudgeFactory

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
    context = EnvironmentContext(config=config, script=script, fn=my_function, render_as_batch=True)
    with DEFAULT_ENGINE.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


run_migrations()


# Mock data for Codeforces API responses
MOCK_CF_CONTESTS = {
    "566": [
        {"contestId": 566, "index": "A", "name": "Matching Names"},
    ],
    "2205": [
        {"contestId": 2205, "index": "G", "name": "Simons and Diophantus Equation"},
    ],
    "2201": [
        {"contestId": 2201, "index": "F1", "name": "Monotone Monochrome Matrices (Medium Version)"},
    ],
    "2185": [
        {"contestId": 2185, "index": "G", "name": "Mixing MEXes"},
        {"contestId": 2185, "index": "D", "name": "OutOfMemoryError"},
    ],
}


class MockCrawler(AbstractCrawler):
    """Mock crawler that returns pre-recorded responses for Codeforces API"""

    def get(self, url: str, *args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200

        if "contest.standings" in url:
            # Extract contestId from URL like ...?contestId=566
            match = re.search(r"contestId=(\d+)", url)
            if match:
                contest_id = match.group(1)
                problems = MOCK_CF_CONTESTS.get(contest_id)
                if problems:
                    content = json.dumps({"status": "OK", "result": {"problems": problems}})
                else:
                    # Unknown contest - simulate CF error
                    content = json.dumps({"status": "FAILED"})
            else:
                content = json.dumps({"status": "FAILED"})
        else:
            content = "{}"

        mock_response.content = content.encode()
        return mock_response


@pytest.fixture(scope="session")
def mock_judge_factory() -> JudgeFactory:
    return JudgeFactory(MockCrawler())


@pytest.fixture(scope="session")
def mocked_app(engine: Engine, mock_judge_factory: JudgeFactory) -> Litestar:
    app = provide_app(
        SQLAlchemyUOWFactory(sessionmaker(bind=engine)), mock_judge_factory
    )
    app.debug = True
    return app

##################################
@pytest.fixture(scope="session")
def engine() -> Engine:
    return create_engine(SQLITE_CONNECTION_STRING)


@pytest.fixture(scope="session")
def uow(engine: Engine) -> Generator[AbstractUnitOfWork, None, None]:
    yield SQLAlchemyUnitOfWork(sessionmaker(bind=engine))
    engine.dispose()


@pytest.fixture(scope="session")
def app(engine: Engine) -> Litestar:
    app = provide_app(
        SQLAlchemyUOWFactory(sessionmaker(bind=engine)), DEFAULT_JUDGE_FACTORY
    )
    app.debug = True
    return app
