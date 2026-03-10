from pathlib import Path

from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures import State
from litestar.template.config import TemplateConfig
from sqlalchemy.orm.session import sessionmaker

from hjudge.commons.db import DEFAULT_ENGINE
from hjudge.commons.db.uow import (
    AbstractUOWFactory,
    SQLAlchemyUOWFactory,
)
from hjudge.lms.endpoints.backend.user import user_endpoints
from hjudge.oj.endpoints.endpoints import all_endpoints as oj_endpoints
from hjudge.oj.models.judges.factory import DEFAULT_JUDGE_FACTORY, JudgeFactory


def provide_uow_factory(uow_factory: AbstractUOWFactory):
    def yield_uow_factory(state: State):
        state["uow_factory"] = uow_factory
        yield uow_factory

    return yield_uow_factory


def provide_judge_factory(judge_factory: JudgeFactory):
    def yield_judge_factory(state: State):
        yield judge_factory

    return yield_judge_factory


def provide_app(uow_factory: AbstractUOWFactory, judge_factory: JudgeFactory):
    return Litestar(
        [] + user_endpoints + oj_endpoints,
        dependencies={
            "uow_factory": provide_uow_factory(uow_factory),
            "judge_factory": provide_judge_factory(judge_factory),
        },
        template_config=TemplateConfig(
            directory=Path("templates"), engine=JinjaTemplateEngine
        ),
    )


app = provide_app(
    SQLAlchemyUOWFactory(sessionmaker(bind=DEFAULT_ENGINE)),
    DEFAULT_JUDGE_FACTORY,
)
