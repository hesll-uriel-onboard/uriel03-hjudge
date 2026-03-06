import json
from copy import copy

import pytest
from litestar import Litestar
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED
from litestar.testing import TestClient
from sqlalchemy import Engine

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.db.repositories.user import AbstractUserRepository
from hjudge.lms.db.tables.user import user_session_table, user_table
from hjudge.lms.models.user import hashed_password


@pytest.fixture(autouse=True, scope="function")
def clear_tables(engine: Engine):
    with engine.connect() as connection:
        connection.execute(user_table.delete())
        connection.execute(user_session_table.delete())
        connection.commit()


def build_user(username: str, password: str, name: str) -> dict[str, str]:
    return {"username": username, "password": password, "name": name}


JSON_ENCODER = json.JSONEncoder()
DEFAULT_USER = build_user("test", "test", "test")


def build_login_request(user: dict[str, str]) -> str:
    request = copy(user)
    request.pop("name")
    return JSON_ENCODER.encode(request)


def build_register_request(user: dict[str, str]) -> str:
    return JSON_ENCODER.encode(user)


@pytest.mark.parametrize("user", [DEFAULT_USER])
def test_register(uow: AbstractUnitOfWork, app: Litestar, user: dict[str, str]):
    # with
    request = build_register_request(user)
    # act
    with TestClient(app=app) as client:
        response = client.post(url="/register", content=request)
    # assert
    assert response.status_code == HTTP_201_CREATED
    assert response.content.decode() == ""

    with uow:
        repository: AbstractUserRepository = uow.create_repository(
            AbstractUserRepository
        )  # pyright: ignore
        result = repository.get_user(user["username"])
        assert result is not None
        result = result.as_model()
    assert result.username == user["username"]
    assert result.password == hashed_password(user["password"])
    assert result.name == user["name"]


@pytest.mark.parametrize(
    "user",
    [DEFAULT_USER],
)
def test_login(app: Litestar, uow: AbstractUnitOfWork, user: dict[str, str]):
    # with
    with TestClient(app=app) as client:
        response = client.post(
            url="/register", content=build_register_request(user)
        )
    # and
    request = build_login_request(user)
    # act
    with TestClient(app=app) as client:
        response = client.post(url="/login", content=request)
        assert response.status_code == HTTP_200_OK


@pytest.mark.parametrize("user", [DEFAULT_USER])
def test_register_duplicated(
    app: Litestar, uow: AbstractUnitOfWork, user: dict[str, str]
):
    # with
    request = build_register_request(user)
    # and
    with TestClient(app=app) as client:
        client.post("/register", content=request)
    # act
    with TestClient(app=app) as client:
        response = client.post("/register", content=request)
    # assert
    assert response.status_code == 409


@pytest.mark.parametrize("user", [DEFAULT_USER])
def test_login_wrong_password(
    app: Litestar, uow: AbstractUnitOfWork, user: dict[str, str]
):
    # with
    request = build_register_request(user)
    # and
    with TestClient(app=app) as client:
        client.post("/register", content=request)
    # act
    with TestClient(app=app) as client:
        response = client.post(
            "/login",
            content=build_login_request(
                build_user(user["username"], "wrong_password", "")
            ),
        )
    # assert
    assert response.status_code == 400
    assert response.content.decode() == "Wrong credentials."


@pytest.mark.parametrize("user", [DEFAULT_USER])
def test_login_unknown_user(
    app: Litestar, uow: AbstractUnitOfWork, user: dict[str, str]
):
    # with
    request = build_register_request(user)
    # and
    with TestClient(app=app) as client:
        client.post("/register", content=request)
    # act
    with TestClient(app=app) as client:
        response = client.post(
            "/login",
            content=build_login_request(
                build_user("whatever", "doesnotmatter", "")
            ),
        )
    # assert
    assert response.status_code == 400
    assert response.content.decode() == "Wrong credentials."
