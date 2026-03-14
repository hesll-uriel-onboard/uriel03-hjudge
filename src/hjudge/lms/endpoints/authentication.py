from uuid import UUID

from litestar import Request, Response

from hjudge.commons.db.uow import AbstractUnitOfWork, AbstractUOWFactory
from hjudge.commons.endpoints.responses import (
    ErrorResponse,
    get_litestar_response,
)
from hjudge.commons.errors import AbstractError, UOWSessionNotFoundError
from hjudge.lms.db.repositories.user import AbstractUserRepository
from hjudge.lms.endpoints.responses.user import COOKIE_KEY
from hjudge.lms.errors import NotAuthorizedError
from hjudge.lms.models.user import User


# def get_user(request: Request, required: bool = True) -> User | None:
#     __temp = request.app.state.get("uow_factory")
#     if __temp is None:
#         raise UOWSessionNotFoundError

#     uow_factory: AbstractUOWFactory = __temp
#     cookie = request.cookies.get(COOKIE_KEY)
#     if cookie is None:
#         return None

#     result = None
#     with uow_factory.create_uow() as uow:
#         repository: AbstractUserRepository = uow.create_repository(
#             AbstractUserRepository
#         )  # pyright: ignore
#         entity = repository.get_user_session(cookie)
#         if entity is None:
#             if not required:
#                 uow.rollback()
#                 return None
#             raise NotAuthorizedError

#         result = entity.user.as_model()
#         uow.rollback()
#     return result


# # def authenticate_user(request: Request) -> Response | None:
#     try:
#         user = get_user(request)
#         if user is None:
#             raise NotAuthorizedError
#         request.query_params["auth_user"] = user

#     except AbstractError as e:
#         return get_litestar_response(ErrorResponse(e))


# def retrieve_user_info(request: Request) -> Response | None:
#     try:
#         user = get_user(request, required=False)
#         request.query_params["auth_user"] = user
#     except AbstractError as e:
#         return get_litestar_response(ErrorResponse(e))


def authenticate_user(
    cookie: str | None, uow: AbstractUnitOfWork, required: bool = True
) -> User | None:
    if cookie is None:
        return None

    result = None
    with uow:
        repository: AbstractUserRepository = uow.create_repository(
            AbstractUserRepository
        )  # pyright: ignore
        entity = repository.get_user_session(cookie)
        if entity is None:
            if not required:
                uow.rollback()
                return None
            raise NotAuthorizedError

        result = entity.user.as_model()
        uow.rollback()
    return result
