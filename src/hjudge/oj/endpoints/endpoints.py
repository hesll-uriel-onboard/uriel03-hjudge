from uuid import UUID

import litestar
from litestar import get, post

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.commons.endpoints.responses import (
    ErrorResponse,
    get_litestar_response,
)
from hjudge.commons.errors import AbstractError
from hjudge.oj.endpoints.requests import SubmitRequest
from hjudge.oj.endpoints.responses import ExerciseResponse, SubmissionResponse
from hjudge.oj.errors import ExerciseNotFoundError, JudgeNotExistedError
from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.judges.factory import JudgeFactory
from hjudge.oj.models.submission import Verdict
from hjudge.oj.services import exercise as exercise_services
from hjudge.oj.services import submission as submission_services


@get("/exercises")
async def check_exercise_existence(
    judge: str,
    code: str,
    judge_factory: JudgeFactory,
    uow: AbstractUnitOfWork,  # judge: JudgeEnum, code: str
) -> litestar.Response:
    try:
        try:
            judge_enum = JudgeEnum(judge)
        except ValueError:
            raise JudgeNotExistedError
        result = exercise_services.check_exercise_existence(
            judge_enum, code, judge_factory, uow
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


@post("/submissions/")
async def submit(
    data: SubmitRequest,
    uow: AbstractUnitOfWork,  # judge: JudgeEnum, code: str
) -> litestar.Response:
    try:
        result = submission_services.submit(
            data.user_id, data.exercise_id, data.verdict, uow
        )
        response = SubmissionResponse(result)
    except AbstractError as e:
        response = ErrorResponse(e)
    return get_litestar_response(response)


@get("/submissions/users/{user_id:str}")
async def get_submissions_from_user(
    user_id: UUID,
    uow: AbstractUnitOfWork,  # judge: JudgeEnum, code: str
) -> litestar.Response:
    raise NotImplementedError


all_endpoints = [check_exercise_existence, submit]
