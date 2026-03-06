from litestar import Response, post
from litestar.datastructures import Cookie
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED

from hjudge.commons.db.uow import AbstractUnitOfWork
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
from hjudge.lms.errors import UserNotFoundError
from hjudge.lms.services import user as user_services


@post("/login")
async def login(uow: AbstractUnitOfWork, data: UserLoginRequest) -> Response:
    # try:
    #     cookie
    response: AbstractResponse
    try:
        cookie = user_services.login(data.username, data.password, uow).cookie
        response = UserLoginResponse(cookie)
    except AbstractError as e:
        response = ErrorResponse(e)

    return get_litestar_response(response)


@post("/register")
async def register(
    uow: AbstractUnitOfWork, data: UserRegisterRequest
) -> Response:
    response: AbstractResponse
    try:
        user_services.register(data.username, data.password, data.name, uow)
        response = UserRegisterResponse()
    except AbstractError as e:
        response = ErrorResponse(e)

    return get_litestar_response(response)


user_endpoints = [login, register]
