import litestar
from litestar import get

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.commons.endpoints.responses import (
    ErrorResponse,
    get_litestar_response,
)
from hjudge.commons.errors import AbstractError
from hjudge.oj.endpoints.responses import ExerciseResponse
from hjudge.oj.errors import ExerciseNotFoundError, JudgeNotExistedError
from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.services import exercise as services


@get("/exercises")
async def check_exercise_existence(
    judge: str,
    code: str,
    uow: AbstractUnitOfWork,  # judge: JudgeEnum, code: str
) -> litestar.Response:
    try:
        try:
            judge_enum = JudgeEnum(judge)
        except ValueError:
            raise JudgeNotExistedError
        result = services.check_exercise_existence(judge_enum, code, uow)
        if result is None:
            response = ErrorResponse(ExerciseNotFoundError())
        else:
            response = ExerciseResponse(result)
    except AbstractError as e:
        response = ErrorResponse(e)
    return get_litestar_response(response)


exercise_endpoints = [check_exercise_existence]
