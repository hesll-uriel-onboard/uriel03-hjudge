from typing import Any
from uuid import UUID

import litestar
from litestar import Request, get, patch, post

from hjudge.commons.db.uow import AbstractUnitOfWork, AbstractUOWFactory
from hjudge.commons.endpoints.responses import (
    ErrorResponse,
    get_litestar_response,
)
from hjudge.commons.errors import AbstractError
from hjudge.lms.endpoints.authentication import authenticate_user
from hjudge.lms.endpoints.responses.user import COOKIE_KEY
from hjudge.lms.errors import NotAuthorizedError
from hjudge.oj.db.repositories.exercise import AbstractExerciseRepository
from hjudge.oj.db.repositories.submission import AbstractSubmissionRepository
from hjudge.oj.endpoints.requests import SubmitRequest, UpdateUserJudgesRequest
from hjudge.oj.endpoints.responses import (
    ExerciseResponse,
    SubmissionsResponse,
    SubmitResponse,
    UserJudgesResponse,
    BatchMaxPointsResponse,
)
from hjudge.oj.errors import ExerciseNotFoundError, JudgeNotExistedError
from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.judges.factory import JudgeFactory
from hjudge.oj.models.submission import Verdict
from hjudge.oj.services import exercise as exercise_services
from hjudge.oj.services import submission as submission_services
from hjudge.oj.services import user_judge as user_judge_services


@get("/api/exercises/{exercise_id:str}")
async def get_exercise_by_id(
    exercise_id: str,
    uow_factory: AbstractUOWFactory,
    judge_factory: JudgeFactory,
) -> litestar.Response:
    try:
        with uow_factory.create_uow() as uow:
            repo: AbstractExerciseRepository = uow.create_repository(
                AbstractExerciseRepository
            )  # pyright: ignore
            entity = repo.get_exercise(UUID(exercise_id))

            if entity is None:
                uow.rollback()
                response = ErrorResponse(ExerciseNotFoundError())
            else:
                exercise = entity.as_model()
                uow.rollback()
                response = ExerciseResponse(
                    exercise=exercise,
                    url=judge_factory.create_from(exercise.judge).get_exercise_url(
                        exercise.code
                    ),
                )
    except AbstractError as e:
        response = ErrorResponse(e)
    return get_litestar_response(response)


@get("/api/exercises")
async def check_exercise_existence(
    query: dict[str, str],
    judge_factory: JudgeFactory,
    uow_factory: AbstractUOWFactory,  # judge: JudgeEnum, code: str
) -> litestar.Response:
    try:
        try:
            judge_enum = JudgeEnum[query["judge"]]
        except Exception:
            raise JudgeNotExistedError
        result = exercise_services.check_exercise_existence(
            judge_enum, query["code"], judge_factory, uow_factory.create_uow()
        )
        if result is None:
            response = ErrorResponse(ExerciseNotFoundError())
        else:
            response = ExerciseResponse(
                exercise=result,
                url=judge_factory.create_from(judge_enum).get_exercise_url(
                    result.code
                ),
            )
    except AbstractError as e:
        response = ErrorResponse(e)
    return get_litestar_response(response)


@post("/api/submissions/", deprecated=True)
async def submit(
    data: SubmitRequest,
    uow_factory: AbstractUOWFactory,  # judge: JudgeEnum, code: str
) -> litestar.Response:
    """Deprecated: Use the crawler to fetch submissions instead."""
    try:
        result = submission_services.submit(
            data.user_id,
            data.exercise_id,
            Verdict[data.verdict],
            uow_factory.create_uow(),
        )
        response = SubmitResponse(result)
    except AbstractError as e:
        response = ErrorResponse(e)
    return get_litestar_response(response)


@get("/api/submissions")
async def get_submissions_from_user_and_exercise(
    query: dict[str, str],
    uow_factory: AbstractUOWFactory,  # judge: JudgeEnum, code: str
    judge_factory: JudgeFactory,
) -> litestar.Response:
    print("okeokeoke")
    user_id = UUID(query["user"])
    exercise_id = UUID(query["exercise"])
    try:
        result = submission_services.get_submissions(
            user_id, exercise_id, uow_factory.create_uow()
        )
        response = SubmissionsResponse(result, judge_factory)
    except AbstractError as e:
        response = ErrorResponse(e)
    return get_litestar_response(response)


@get("/api/submissions/batch")
async def get_batch_max_points(
    query: dict[str, str],
    uow_factory: AbstractUOWFactory,
) -> litestar.Response:
    """Get max points for multiple exercises for a single user.

    Query params:
        user: user_id (required)
        exercises: comma-separated list of exercise_ids (required)
    """
    try:
        user_id = UUID(query["user"])
        exercise_ids = [UUID(eid) for eid in query.get("exercises", "").split(",") if eid]

        if not exercise_ids:
            response = BatchMaxPointsResponse({})
        else:
            with uow_factory.create_uow() as uow:
                submission_repo: AbstractSubmissionRepository = uow.create_repository(
                    AbstractSubmissionRepository
                )  # pyright: ignore
                max_points = submission_repo.get_max_points_by_exercise_and_user(
                    exercise_ids, [user_id]
                )
                # Convert to exercise_id -> points mapping
                result = {
                    str(exercise_id): max_points.get((exercise_id, user_id), 0)
                    for exercise_id in exercise_ids
                }
                response = BatchMaxPointsResponse(result)
    except AbstractError as e:
        response = ErrorResponse(e)
    return get_litestar_response(response)


@get("/api/users/judges")
async def get_user_judges(
    request: Request,
    uow_factory: AbstractUOWFactory,
) -> litestar.Response:
    """Get all judge handles for the authenticated user."""
    cookie = request.cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=True)
    if user is None:
        return get_litestar_response(ErrorResponse(NotAuthorizedError()))
    result = user_judge_services.get_user_judges(user.id, uow_factory.create_uow())
    return get_litestar_response(UserJudgesResponse(result))


@patch("/api/users/judges")
async def update_user_judges(
    request: Request,
    data: UpdateUserJudgesRequest,
    uow_factory: AbstractUOWFactory,
) -> litestar.Response:
    """Update the authenticated user's judge handles."""
    cookie = request.cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=True)
    if user is None:
        return get_litestar_response(ErrorResponse(NotAuthorizedError()))
    judges = [(pair.judge, pair.handle) for pair in data.judges]
    result = user_judge_services.update_user_judges(
        user.id, judges, uow_factory.create_uow()
    )
    return get_litestar_response(UserJudgesResponse(result))


all_endpoints = [
    get_exercise_by_id,
    check_exercise_existence,
    get_submissions_from_user_and_exercise,
    get_batch_max_points,
    get_user_judges,
    update_user_judges,
]
