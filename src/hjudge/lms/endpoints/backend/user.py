from litestar import Request, Response, post

from hjudge.commons.db.uow import AbstractUOWFactory
from hjudge.commons.endpoints.responses import (
    AbstractResponse,
    ErrorResponse,
    get_litestar_response,
)
from hjudge.commons.errors import AbstractError
from hjudge.lms.endpoints.frontend.user import home
from hjudge.lms.endpoints.requests.user import (
    UserLoginRequest,
    UserRegisterRequest,
)
from hjudge.lms.endpoints.responses.user import (
    COOKIE_KEY,
    UserLoginResponse,
    UserLogoutResponse,
    UserRegisterResponse,
)
from hjudge.lms.services import user as user_services


@post("/api/login")
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


@post("/api/register")
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


@post("/api/logout")
async def logout(request: Request, uow_factory: AbstractUOWFactory) -> Response:
    cookie = request.cookies.get(COOKIE_KEY)
    if cookie:
        user_services.logout(cookie, uow_factory.create_uow())
    return get_litestar_response(UserLogoutResponse())