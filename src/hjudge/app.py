import os
from pathlib import Path

from hjudge.oj.endpoints.frontend import lms_frontends
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
from hjudge.lms.endpoints.endpoints import lms_endpoints
from hjudge.oj.endpoints.endpoints import all_endpoints as oj_endpoints
from hjudge.oj.models.judges.factory import DEFAULT_JUDGE_FACTORY, JudgeFactory


def yield_uow_factory(state: State):
    yield state["uow_factory"]


def yield_judge_factory(state: State):
    yield state["judge_factory"]


def provide_app(uow_factory: AbstractUOWFactory, judge_factory: JudgeFactory):
    return Litestar(
        [] + lms_endpoints + oj_endpoints + lms_frontends,
        dependencies={
            "uow_factory": yield_uow_factory,
            "judge_factory": yield_judge_factory,
        },
        template_config=TemplateConfig(
            directory=Path(__file__).parent / "templates",
            engine=JinjaTemplateEngine,
        ),
        state=State(
            {"uow_factory": uow_factory, "judge_factory": judge_factory}
        ),
    )


app = provide_app(
    SQLAlchemyUOWFactory(sessionmaker(bind=DEFAULT_ENGINE)),
    DEFAULT_JUDGE_FACTORY,
)
