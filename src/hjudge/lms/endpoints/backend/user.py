from litestar import Response, post

from hjudge.commons.db.uow import AbstractUnitOfWork, AbstractUOWFactory
from hjudge.commons.endpoints.responses import (
    AbstractResponse,
    ErrorResponse,
    get_litestar_response,
)
from hjudge.commons.errors import AbstractError
from hjudge.lms.endpoints.requests.user import (
    UserLoginRequest,
    UserRegisterRequest,
)
from hjudge.lms.endpoints.responses.user import (
    UserLoginResponse,
    UserRegisterResponse,
)
from hjudge.lms.services import user as user_services


@post("/login")
async def login(
    uow_factory: AbstractUOWFactory, data: UserLoginRequest
) -> Response:
    # try:
    #     cookie
    response: AbstractResponse
    try:
        cookie = user_services.login(
            data.username, data.password, uow_factory.create_uow()
        ).cookie
        response = UserLoginResponse(cookie)
    except AbstractError as e:
        response = ErrorResponse(e)

    return get_litestar_response(response)


@post("/register")
async def register(
    uow_factory: AbstractUOWFactory, data: UserRegisterRequest
) -> Response:
    response: AbstractResponse
    try:
        user_services.register(
            data.username, data.password, data.name, uow_factory.create_uow()
        )
        response = UserRegisterResponse()
    except AbstractError as e:
        response = ErrorResponse(e)

    return get_litestar_response(response)


user_endpoints = [login, register]
