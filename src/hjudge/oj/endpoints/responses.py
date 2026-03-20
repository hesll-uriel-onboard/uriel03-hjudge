from typing import Dict, List, override

from hjudge.commons.endpoints.responses import AbstractResponse
from hjudge.commons.endpoints.status_codes import HTTP_200_OK
from hjudge.oj.models.judges import Exercise
from hjudge.oj.models.judges.factory import JudgeFactory
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
    def __init__(
        self, submissions: List[Submission], judge_factory: JudgeFactory
    ):
        result = []
        for submission in submissions:
            submission_dict = submission.model_dump()
            judge = judge_factory.create_from(submission.exercise.judge)
            submission_dict["url"] = judge.get_submission_url(
                submission_id=submission.submission_id,
                code=submission.exercise.code,
            )
            result.append(submission_dict)
        super().__init__(status_code=HTTP_200_OK, content=result)


class BatchMaxPointsResponse(AbstractResponse):
    @override
    def __init__(self, max_points: Dict[str, int]):
        """Response for batch max points query.

        Args:
            max_points: Dict mapping exercise_id (as string) -> max_points
        """
        super().__init__(status_code=HTTP_200_OK, content=max_points)


class UserJudgesResponse(AbstractResponse):
    @override
    def __init__(self, user_judges: List[UserJudge]):
        result = [uj.model_dump(mode="json") for uj in user_judges]
        super().__init__(status_code=HTTP_200_OK, content=result)
