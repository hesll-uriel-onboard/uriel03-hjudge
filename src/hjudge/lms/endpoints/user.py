from litestar import Request, post

from hjudge.lms.db.uow import AbstractUnitOfWork
from hjudge.lms.endpoints import OK_RESPONSE
from hjudge.lms.endpoints.requests.user import (
    UserLoginRequest,
    UserRegisterRequest,
)
from hjudge.lms.services import user as user_services


@post("/login")
async def login(uow: AbstractUnitOfWork, data: UserLoginRequest) -> str:
    return user_services.login(data.username, data.password, uow).cookie


@post("/register")
async def register(uow: AbstractUnitOfWork, data: UserRegisterRequest) -> dict:
    user_services.register(data.username, data.password, data.name, uow)
    return OK_RESPONSE


user_endpoints = [login, register]
