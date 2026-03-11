from typing import Any

from litestar import MediaType, get
from litestar.datastructures import Cookie, State
from litestar.response import Template

from hjudge.commons.db.uow import AbstractUOWFactory
from hjudge.lms.endpoints.authentication import authenticate_user
from hjudge.lms.endpoints.responses.user import COOKIE_KEY


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
