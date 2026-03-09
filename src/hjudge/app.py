from litestar import Litestar
from litestar.datastructures import State
from sqlalchemy.orm.session import sessionmaker

from hjudge.commons.db import DEFAULT_ENGINE
from hjudge.commons.db.uow import AbstractUnitOfWork, SQLAlchemyUnitOfWork
from hjudge.lms.endpoints.user import user_endpoints
from hjudge.oj.endpoints.endpoints import all_endpoints as oj_endpoints
from hjudge.oj.models.judges.factory import DEFAULT_JUDGE_FACTORY, JudgeFactory


def provide_uow(uow: AbstractUnitOfWork):
    def yield_uow(state: State):
        yield uow

    return yield_uow


def provide_judge_factory(judge_factory: JudgeFactory):
    def yield_judge_factory(state: State):
        yield judge_factory

    return yield_judge_factory


def provide_app(uow: AbstractUnitOfWork, judge_factory: JudgeFactory):
    return Litestar(
        [] + user_endpoints + oj_endpoints,
        dependencies={
            "uow": provide_uow(uow),
            "judge_factory": provide_judge_factory(judge_factory),
        },
    )


app = provide_app(
    SQLAlchemyUnitOfWork(sessionmaker(bind=DEFAULT_ENGINE)),
    DEFAULT_JUDGE_FACTORY,
)
