import pytest
from sqlalchemy import Engine

from hjudge.commons.db.uow import AbstractUnitOfWork, SQLAlchemyUnitOfWork
from hjudge.commons.errors import UOWSessionNotFoundError
from hjudge.lms.db.repositories.user import (
    AbstractUserRepository,
    SQLAlchemyUserRepository,
)
from hjudge.lms.db.tables.user import user_session_table, user_table
from hjudge.lms.models.user import User
from tests.conftest import engine


@pytest.fixture(autouse=True)
def clear_tables(engine: Engine):
    with engine.connect() as connection:
        connection.execute(user_table.delete())
        connection.execute(user_session_table.delete())
        connection.commit()


def test_add_a_user(uow: AbstractUnitOfWork):
    with uow:
        user_repo: SQLAlchemyUserRepository = uow.create_repository(
            AbstractUserRepository
        )  # pyright: ignore
        user = User(username="test", password="test", name="test")
        user_repo.add_user(user)
        uow.commit()

    result = user_repo.get_user(user.username)
    assert result is not None
    assert result == user


def test_add_a_user_session(uow: AbstractUnitOfWork):
    with uow:
        user_repo: SQLAlchemyUserRepository = uow.create_repository(
            AbstractUserRepository
        )  # pyright: ignore
        user = User(username="test", password="test", name="test")

        user_repo.add_user(user)
        uow.commit()

    result = user_repo.get_user(user.username)
    assert result is not None
    assert result == user
