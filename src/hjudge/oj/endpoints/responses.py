from typing import override

from hjudge.commons.endpoints.responses import AbstractResponse
from hjudge.commons.endpoints.status_codes import HTTP_200_OK
from hjudge.oj.models.judges import Exercise
from hjudge.oj.models.submission import Submission


class ExerciseResponse(AbstractResponse):
    @override
    def __init__(self, exercise: Exercise, url: str):
        result = exercise.model_dump()
        result["url"] = url
        super().__init__(status_code=HTTP_200_OK, content=result)


class SubmissionResponse(AbstractResponse):
    @override
    def __init__(self, submission: Submission):
        result = submission.model_dump()
        super().__init__(status_code=HTTP_200_OK, content=result)
