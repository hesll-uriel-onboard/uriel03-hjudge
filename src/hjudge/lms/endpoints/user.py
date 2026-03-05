from litestar import Response, post
from litestar.datastructures import Cookie
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.endpoints import COOKIE_NAME
from hjudge.lms.endpoints.requests.user import (
    UserLoginRequest,
    UserRegisterRequest,
)
from hjudge.lms.services import user as user_services


@post("/login")
async def login(uow: AbstractUnitOfWork, data: UserLoginRequest) -> Response:
    return Response(
        "",
        cookies=[
            Cookie(
                key=COOKIE_NAME,
                value=user_services.login(
                    data.username, data.password, uow
                ).cookie,
            )
        ],
        status_code=HTTP_200_OK,
    )


@post("/register")
async def register(
    uow: AbstractUnitOfWork, data: UserRegisterRequest
) -> Response:
    user_services.register(data.username, data.password, data.name, uow)
    return Response("", status_code=HTTP_201_CREATED)


user_endpoints = [login, register]
