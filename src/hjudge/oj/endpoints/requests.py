from uuid import UUID

from pydantic import BaseModel

from hjudge.oj.models.judges import JudgeEnum


class ExerciseRequest(BaseModel):
    judge: JudgeEnum
    code: str


class SubmitRequest(BaseModel):
    user_id: UUID
    exercise_id: UUID
    verdict: str


class JudgeHandlePair(BaseModel):
    judge: JudgeEnum
    handle: str


class UpdateUserJudgesRequest(BaseModel):
    judges: list[JudgeHandlePair]
