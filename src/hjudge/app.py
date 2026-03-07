from hjudge.oj.endpoints.exercise import exercise_endpoints
from litestar import Litestar
from litestar.datastructures import State
from sqlalchemy.orm.session import sessionmaker

from hjudge.commons.db import DEFAULT_ENGINE
from hjudge.commons.db.uow import AbstractUnitOfWork, SQLAlchemyUnitOfWork
from hjudge.lms.endpoints.user import user_endpoints


def provide_uow(uow: AbstractUnitOfWork):
    def yield_uow(state: State):
        yield uow

    return yield_uow


def provide_app(uow: AbstractUnitOfWork):
    return Litestar([] + user_endpoints + exercise_endpoints, dependencies={"uow": provide_uow(uow)})


app = provide_app(SQLAlchemyUnitOfWork(sessionmaker(bind=DEFAULT_ENGINE)))
