"""Test services.

As I decide that the two login exceptions will have
the same code and msg, this shall be tested separately.
"""

import pytest
import sqlalchemy as sa

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.db.tables.user import user_session_table, user_table
from hjudge.lms.errors import (
    UserNotFoundError,
    UserWrongPasswordError,
)
from hjudge.lms.services.user import login, register
from tests.conftest import engine, session_factory, uow

USERNAME = "test"
PASSWORD = "test"
NAME = "test"


def make_a_user_request(
    username: str = USERNAME, password: str = PASSWORD, name: str = NAME
) -> dict[str, str]:
    return {
        "username": username,
        "password": password,
        "name": name,
    }


@pytest.fixture(autouse=True, scope="function")
def clear_tables(engine: sa.Engine):
    with engine.connect() as connection:
        connection.execute(user_table.delete())
        connection.execute(user_session_table.delete())
        connection.commit()


def test_login_wrong_password(uow: AbstractUnitOfWork):
    # with
    user = make_a_user_request()
    user = register(user["username"], user["password"], user["name"], uow)
    # and
    WRONG_PASSWORD = "wrong_password"
    # do and assert
    with pytest.raises(UserWrongPasswordError):
        login(user.username, WRONG_PASSWORD, uow)


def test_login_unknown_user(uow: AbstractUnitOfWork):
    # with
    user = make_a_user_request()
    user = register(user["username"], user["password"], user["name"], uow)

    # do
    with pytest.raises(UserNotFoundError):
        login("whatever", "whatever", uow)
