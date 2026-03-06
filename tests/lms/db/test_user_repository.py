import pytest
from sqlalchemy import Engine

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.db.repositories.user import (
    AbstractUserRepository,
    SQLAlchemyUserRepository,
)
from hjudge.lms.db.tables.user import user_session_table, user_table
from hjudge.lms.models.converters import (
    as_user_entity,
    as_user_session_entity,
)
from hjudge.lms.models.user import User, UserSession
from tests.conftest import engine, session_factory


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

        user_repo.add_user(as_user_entity(user))
        uow.commit()

        result = user_repo.get_user(user.username)
        assert result is not None
        assert result.as_model() == user


def test_add_a_user_session(uow: AbstractUnitOfWork):
    # with
    with uow:
        user = User(username="test", password="test", name="test")
        user_repo: SQLAlchemyUserRepository = uow.create_repository(
            AbstractUserRepository
        )  # pyright: ignore
        user_repo.add_user(as_user_entity(user))
        uow.commit()
    # act
    with uow:
        user_session = UserSession(user=user)
        user_repo = uow.create_repository(
            AbstractUserRepository
        )  # pyright: ignore
        user_repo.add_user_session(as_user_session_entity(user_session))
        uow.commit()
    # assert
    with uow:
        print(user_session)
        result = user_repo.get_user_session(user_session.cookie)
        assert result is not None
        assert result.as_model() == user_session
        uow.commit()
