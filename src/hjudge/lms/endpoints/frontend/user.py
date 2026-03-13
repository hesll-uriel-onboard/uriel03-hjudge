from typing import Any

from litestar import MediaType, get
from litestar.datastructures import Cookie, State
from litestar.response import Template

from hjudge.commons.db.uow import AbstractUOWFactory
from hjudge.lms.endpoints.authentication import authenticate_user
from hjudge.lms.endpoints.responses.user import COOKIE_KEY
from hjudge.oj.db.repositories.user_judge import AbstractUserJudgeRepository


@get(
    ["/", "/home"],
    media_type=MediaType.HTML,
    include_in_schema=False,
)
async def home(
    cookies: dict[str, str],
    query: dict[str, Any],
    uow_factory: AbstractUOWFactory,
) -> Template:
    cookie: str | None = cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=False)
    return Template(
        template_name="views/home.jinja",
        context={"user": user},
    )


@get("/register", media_type=MediaType.HTML, include_in_schema=False)
async def register() -> Template:
    return Template(template_name="views/register.jinja")


@get("/login", media_type=MediaType.HTML, include_in_schema=False)
async def login() -> Template:
    return Template(template_name="views/login.jinja")


@get("/profile", media_type=MediaType.HTML, include_in_schema=False)
async def profile(
    cookies: dict[str, str],
    uow_factory: AbstractUOWFactory,
) -> Template:
    """Profile page for managing judge handles."""
    cookie: str | None = cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=True)

    # Get existing judge handles
    with uow_factory.create_uow() as uow:
        repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        entities = repo.list_by_user(user.id)
        user_judges = [e.as_model() for e in entities]
        uow.rollback()

    return Template(
        template_name="views/profile.jinja",
        context={"user": user, "user_judges": user_judges},
    )
