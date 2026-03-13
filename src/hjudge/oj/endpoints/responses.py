from typing import List, override

from hjudge.commons.endpoints.responses import AbstractResponse
from hjudge.commons.endpoints.status_codes import HTTP_200_OK
from hjudge.oj.models.judges import Exercise
from hjudge.oj.models.submission import Submission
from hjudge.oj.models.user_judge import UserJudge


class ExerciseResponse(AbstractResponse):
    @override
    def __init__(self, exercise: Exercise, url: str):
        result = exercise.model_dump()
        result["url"] = url
        super().__init__(status_code=HTTP_200_OK, content=result)


class SubmitResponse(AbstractResponse):
    @override
    def __init__(self, submission: Submission):
        result = submission.model_dump()
        super().__init__(status_code=HTTP_200_OK, content=result)


class SubmissionsResponse(AbstractResponse):
    @override
    def __init__(self, submissions: List[Submission]):
        result = [submission.model_dump() for submission in submissions]
        super().__init__(status_code=HTTP_200_OK, content=result)


class UserJudgesResponse(AbstractResponse):
    @override
    def __init__(self, user_judges: List[UserJudge]):
        result = [uj.model_dump(mode="json") for uj in user_judges]
        super().__init__(status_code=HTTP_200_OK, content=result)
