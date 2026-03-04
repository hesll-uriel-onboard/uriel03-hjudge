from litestar import Litestar
from litestar.datastructures import State

from hjudge.lms.db.factory import DEFAULT_ENGINE
from hjudge.lms.db.uow import SQLAlchemyUnitOfWork
from hjudge.lms.endpoints.user import user_endpoints


def provide_uow(state: State):
    yield SQLAlchemyUnitOfWork(DEFAULT_ENGINE)


app = Litestar(
    [] + user_endpoints,
    dependencies={"uow": provide_uow},
)
