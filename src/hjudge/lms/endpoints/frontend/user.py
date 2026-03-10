from litestar import Request

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.commons.endpoints.responses import ErrorResponse


def authenticate(request: Request) -> ErrorResponse | None:
    uow: AbstractUnitOfWork = request.state["uow"]
    with uow