"""Test services.

As I decide that the two login exceptions will have
the same code and msg, this shall be tested separately.
"""

import pytest
import sqlalchemy as sa

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.db.tables import user_session_table, user_table
from hjudge.lms.errors import (
    UserNotFoundError,
    UserWrongPasswordError,
)
from hjudge.lms.services.user import login, logout, register

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


def test_logout_deactivates_session(uow: AbstractUnitOfWork, engine: sa.Engine):
    """Test that logout deactivates the user session."""
    # given: a registered user with an active session
    user = register(USERNAME, PASSWORD, NAME, uow)
    session = login(USERNAME, PASSWORD, uow)
    cookie = session.cookie

    # when: the user logs out
    logout(cookie, uow)

    # then: the session should be deactivated
    with engine.connect() as connection:
        result = connection.execute(
            sa.select(user_session_table.c.active).where(
                user_session_table.c.cookie == cookie
            )
        ).scalar_one()
        assert result is False


def test_logout_with_nonexistent_cookie_does_not_raise(
    uow: AbstractUnitOfWork,
):
    """Test that logout with a non-existent cookie does not raise an error."""
    # given: a non-existent cookie
    fake_cookie = "non-existent-cookie"

    # when/then: logout should not raise an error
    logout(fake_cookie, uow)  # should not raise


def test_logout_session_not_found_after_logout(
    uow: AbstractUnitOfWork, engine: sa.Engine
):
    """Test that a deactivated session cannot be used to authenticate."""
    # given: a registered user with an active session
    register(USERNAME, PASSWORD, NAME, uow)
    session = login(USERNAME, PASSWORD, uow)
    cookie = session.cookie

    # when: the user logs out
    logout(cookie, uow)

    # then: get_user_session with the same cookie should return None
    from hjudge.lms.db.repositories.user import SQLAlchemyUserRepository

    with uow:
        repo = SQLAlchemyUserRepository(session=uow._session)  # type: ignore
        result = repo.get_user_session(cookie)
        uow.rollback()
        assert result is None
