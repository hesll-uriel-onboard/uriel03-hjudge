import os
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
from hjudge.oj.services.crawler import crawl_all_users

# Scheduler instance
scheduler = AsyncIOScheduler()


def yield_uow_factory(state: State):
    yield state["uow_factory"]


def yield_judge_factory(state: State):
    yield state["judge_factory"]


async def run_crawler(state: State):
    """Background task to crawl user submissions."""
    uow_factory: AbstractUOWFactory = state["uow_factory"]
    judge_factory: JudgeFactory = state["judge_factory"]
    await crawl_all_users(uow_factory.create_uow(), judge_factory)


def on_startup(app: Litestar):
    """Start the scheduler when the app starts."""
    # Schedule crawler to run every minute
    scheduler.add_job(
        run_crawler,
        "interval",
        minutes=1,
        args=[app.state],
        id="crawl_user_submissions",
        replace_existing=True,
    )
    scheduler.start()


def on_shutdown(app: Litestar):
    """Stop the scheduler when the app shuts down."""
    scheduler.shutdown()


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
        on_startup=[on_startup],
        on_shutdown=[on_shutdown],
    )


app = provide_app(
    SQLAlchemyUOWFactory(sessionmaker(bind=DEFAULT_ENGINE)),
    DEFAULT_JUDGE_FACTORY,
)
