"""Dashboard API endpoints."""

from uuid import UUID

import litestar
from litestar import Request, get

from hjudge.commons.db.uow import AbstractUOWFactory
from hjudge.commons.endpoints.responses import (
    ErrorResponse,
    get_litestar_response,
)
from hjudge.commons.errors import AbstractError
from hjudge.lms.endpoints.authentication import authenticate_user
from hjudge.lms.endpoints.responses.dashboard import (
    LeaderboardResponse,
    ProgressEntryResponse,
)
from hjudge.lms.endpoints.responses.user import COOKIE_KEY
from hjudge.lms.errors import NotAuthorizedError
from hjudge.lms.services import dashboard as dashboard_services


@get("/api/dashboard/lesson/{lesson_id:str}")
async def get_lesson_progress(
    lesson_id: str,
    request: Request,
    uow_factory: AbstractUOWFactory,
) -> litestar.Response:
    """Get the logged-in user's progress for a lesson."""
    cookie = request.cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=False)
    if user is None:
        return get_litestar_response(ErrorResponse(NotAuthorizedError()))

    try:
        progress = dashboard_services.get_progress_for_lesson(
            user.id, UUID(lesson_id), uow_factory.create_uow()
        )
        response = ProgressEntryResponse(progress)
    except AbstractError as e:
        response = ErrorResponse(e)
    return get_litestar_response(response)


@get("/api/dashboard/lesson/{lesson_id:str}/leaderboard")
async def get_lesson_leaderboard(
    lesson_id: str,
    uow_factory: AbstractUOWFactory,
) -> litestar.Response:
    """Get leaderboard for a lesson. Public endpoint."""
    try:
        leaderboard = dashboard_services.get_leaderboard_for_lesson(
            UUID(lesson_id), uow_factory.create_uow()
        )
        response = LeaderboardResponse(leaderboard)
    except AbstractError as e:
        response = ErrorResponse(e)
    return get_litestar_response(response)


@get("/api/dashboard/course/{course_id:str}")
async def get_course_progress(
    course_id: str,
    request: Request,
    uow_factory: AbstractUOWFactory,
) -> litestar.Response:
    """Get the logged-in user's progress for a course."""
    cookie = request.cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=False)
    if user is None:
        return get_litestar_response(ErrorResponse(NotAuthorizedError()))

    try:
        progress = dashboard_services.get_progress_for_course(
            user.id, UUID(course_id), uow_factory.create_uow()
        )
        response = ProgressEntryResponse(progress)
    except AbstractError as e:
        response = ErrorResponse(e)
    return get_litestar_response(response)


@get("/api/dashboard/course/{course_id:str}/leaderboard")
async def get_course_leaderboard(
    course_id: str,
    uow_factory: AbstractUOWFactory,
) -> litestar.Response:
    """Get leaderboard for a course. Public endpoint."""
    try:
        leaderboard = dashboard_services.get_leaderboard_for_course(
            UUID(course_id), uow_factory.create_uow()
        )
        response = LeaderboardResponse(leaderboard)
    except AbstractError as e:
        response = ErrorResponse(e)
    return get_litestar_response(response)


all_endpoints = [
    get_lesson_progress,
    get_lesson_leaderboard,
    get_course_progress,
    get_course_leaderboard,
]