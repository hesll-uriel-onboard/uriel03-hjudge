import pytest
import sqlalchemy as sa

from hjudge.lms.db.tables.user import user_session_table, user_table
from hjudge.lms.db.uow import AbstractUnitOfWork
from hjudge.lms.errors import (
    UserExistedError,
    UserNotFoundError,
    UserWrongPasswordError,
)
from hjudge.lms.models.user import User
from hjudge.lms.services.user import login, register
from tests.conftest import engine

USERNAME = "test"
PASSWORD = "test"
NAME = "test"


def make_a_user(
    username: str = USERNAME, password: str = PASSWORD, name: str = NAME
) -> User:
    return User(
        username=username,
        password=password,
        name=name,
    )


@pytest.fixture(autouse=True, scope="function")
def clear_tables(engine: sa.Engine):
    print("=======in=======")
    with engine.connect() as connection:
        connection.execute(user_table.delete())
        connection.execute(user_session_table.delete())
        connection.commit()
    print("=======out=======")


def test_register(uow: AbstractUnitOfWork):
    """Make a random user, register, and check the returned user"""
    # with
    user = make_a_user()
    # do
    result = register(user.username, user.password, user.name, uow)
    # assert
    assert result.id is not None
    assert result.username == user.username
    assert result.password == user.password
    assert result.name == user.name


def test_register_duplicated(uow: AbstractUnitOfWork):
    # with
    user = make_a_user()
    # do
    register(user.username, user.password, user.name, uow)
    # do and assert
    with pytest.raises(UserExistedError):
        register(user.username, user.password, user.name, uow)


def test_login(uow: AbstractUnitOfWork):
    # with
    user = make_a_user()
    user = register(user.username, user.password, user.name, uow)
    # do
    result = login(user.username, user.password, uow)
    # assert
    assert result.user == user
    assert result.cookie is not None
    assert result.active


def test_login_wrong_password(uow: AbstractUnitOfWork):
    # with
    user = make_a_user()
    user = register(user.username, user.password, user.name, uow)
    # and
    WRONG_PASSWORD = "wrong_password"
    # do and assert
    with pytest.raises(UserWrongPasswordError):
        login(user.username, WRONG_PASSWORD, uow)


def test_login_unknown_user(uow: AbstractUnitOfWork):
    # with
    user = make_a_user()
    user = register(user.username, user.password, user.name, uow)

    # do
    with pytest.raises(UserNotFoundError):
        login("whatever", "whatever", uow)
