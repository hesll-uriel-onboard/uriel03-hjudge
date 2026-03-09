import litestar
from litestar import get, post

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.commons.endpoints.responses import (
    ErrorResponse,
    get_litestar_response,
)
from hjudge.commons.errors import AbstractError
from hjudge.oj.endpoints.responses import ExerciseResponse
from hjudge.oj.errors import ExerciseNotFoundError, JudgeNotExistedError
from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.judges.factory import JudgeFactory
from hjudge.oj.services import exercise as services


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
        result = services.check_exercise_existence(judge_enum, code, uow)
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


@post("/submissions/{exercise_id:str}")
async def submit(
    exercise_id: str,
    uow: AbstractUnitOfWork,  # judge: JudgeEnum, code: str
) -> litestar.Response:
    raise NotImplementedError


all_endpoints = [check_exercise_existence]
