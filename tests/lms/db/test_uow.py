import pytest
from sqlalchemy import Engine

from hjudge.lms.db.repositories.user import (
    AbstractUserRepository,
    SQLAlchemyUserRepository,
)
from hjudge.lms.db.tables.user import user_session_table, user_table
from hjudge.lms.db.uow import AbstractUnitOfWork, SQLAlchemyUnitOfWork
from hjudge.lms.errors import UOWSessionNotFoundError
from hjudge.lms.models.user import User
from tests.conftest import DEFAULT_ENGINE


@pytest.fixture
def engine() -> Engine:
    return DEFAULT_ENGINE


@pytest.fixture
def uow(engine) -> SQLAlchemyUnitOfWork:
    uow = SQLAlchemyUnitOfWork(engine)
    with uow:
        uow.current_session.execute(user_table.delete())
        uow.current_session.execute(user_session_table.delete())
        uow.commit()
    return uow


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


def test_access_to_current_session_without_entering(uow: SQLAlchemyUnitOfWork):
    with pytest.raises(UOWSessionNotFoundError):
        uow.current_session
