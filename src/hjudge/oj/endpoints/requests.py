from uuid import UUID

from pydantic import BaseModel

from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.submission import Verdict


class ExerciseRequest(BaseModel):
    judge: JudgeEnum
    code: str


class SubmissionRequest(BaseModel):
    user_id: UUID
    exercise_id: UUID
    verdict: Verdict
