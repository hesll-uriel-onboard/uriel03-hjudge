from typing import override

from hjudge.commons.endpoints.responses import AbstractResponse
from hjudge.commons.endpoints.status_codes import HTTP_200_OK
from hjudge.oj.models.judges import Exercise
from hjudge.oj.models.judges.factory import JudgeFactory


class ExerciseResponse(AbstractResponse):
    @override
    def __init__(self, exercise: Exercise):
        result = exercise.model_dump()
        result["url"] = JudgeFactory.create_from(exercise.judge).get_exercise_url(
            exercise.code
        )
        super().__init__(status_code=HTTP_200_OK, content=result)
