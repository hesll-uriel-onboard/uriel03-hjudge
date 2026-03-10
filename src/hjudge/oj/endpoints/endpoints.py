from typing import Any
from uuid import UUID

import litestar
from litestar import get, post

from hjudge.commons.db.uow import AbstractUnitOfWork, AbstractUOWFactory
from hjudge.commons.endpoints.responses import (
    ErrorResponse,
    get_litestar_response,
)
from hjudge.commons.errors import AbstractError
from hjudge.oj.endpoints.requests import SubmitRequest
from hjudge.oj.endpoints.responses import (
    ExerciseResponse,
    SubmissionsResponse,
    SubmitResponse,
)
from hjudge.oj.errors import ExerciseNotFoundError, JudgeNotExistedError
from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.judges.factory import JudgeFactory
from hjudge.oj.models.submission import Verdict
from hjudge.oj.services import exercise as exercise_services
from hjudge.oj.services import submission as submission_services


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


@post("/api/submissions/")
async def submit(
    data: SubmitRequest,
    uow_factory: AbstractUOWFactory,  # judge: JudgeEnum, code: str
) -> litestar.Response:
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
) -> litestar.Response:
    print("okeokeoke")
    user_id = UUID(query["user"])
    exercise_id = UUID(query["exercise"])
    try:
        result = submission_services.get_submissions(
            user_id, exercise_id, uow_factory.create_uow()
        )
        response = SubmissionsResponse(result)
    except AbstractError as e:
        response = ErrorResponse(e)
    return get_litestar_response(response)


all_endpoints = [
    check_exercise_existence,
    submit,
    get_submissions_from_user_and_exercise,
]
