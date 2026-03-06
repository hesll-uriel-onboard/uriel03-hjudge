import pytest
from litestar import Litestar
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED
from litestar.testing import TestClient
from sqlalchemy import Engine

from hjudge.app import provide_app
from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.db.tables.user import user_session_table, user_table
from hjudge.lms.endpoints.requests.user import (
    UserLoginRequest,
    UserRegisterRequest,
)
from hjudge.lms.models.user import User
from hjudge.lms.services.user import register
from tests.conftest import engine, uow


@pytest.fixture(autouse=True, scope="function")
def clear_tables(engine: Engine):
    print("=======in=======")
    with engine.connect() as connection:
        connection.execute(user_table.delete())
        connection.execute(user_session_table.delete())
        connection.commit()
    print("=======out=======")


@pytest.fixture
def app(uow) -> Litestar:
    app = provide_app(uow)
    app.debug = True
    return app


@pytest.fixture
def client(app):
    with TestClient(app=app) as client:
        yield


def test_register(app: Litestar):
    with TestClient(app=app) as client:
        response = client.post(
            url="/register",
            content=UserRegisterRequest(
                username="test", password="test", name="test"
            ).model_dump_json(),
        )
        assert response.status_code == HTTP_201_CREATED


@pytest.mark.parametrize(
    "user_login_request",
    [UserLoginRequest(username="test", password="test")],
)
def test_login(
    app: Litestar, uow: AbstractUnitOfWork, user_login_request: UserLoginRequest
):
    # with
    user = User(username="test", password="test", name="test")
    register(user.username, user.password, user.name, uow)
    # and
    user_login_request = UserLoginRequest(
        username=user.username, password=user.password
    )
    # act
    with TestClient(app=app) as client:
        response = client.post(
            url="/login", content=user_login_request.model_dump_json()
        )
        assert response.status_code == HTTP_200_OK
