from pydantic import BaseModel

from hjudge.oj.models.judges import JudgeEnum


class ExerciseRequest(BaseModel):
    judge: JudgeEnum
    code: str
