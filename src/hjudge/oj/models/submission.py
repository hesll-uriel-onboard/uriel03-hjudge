from datetime import datetime
from enum import Enum

from pydantic import UUID4, Field
from typing_extensions import deprecated

from hjudge.commons.models import Base
from hjudge.oj.models.judges import Exercise, JudgeEnum


class Verdict(Enum):
    AC = "Accepted"
    WA = "Wrong Answer"
    TLE = "Time Limit Exceeded"
    RTE = "Run-Time Error"


@deprecated("Will be use eventually")
class UserJudge(Base):
    user_id: UUID4
    judge: JudgeEnum
    handle: str


class Submission(Base):
    exercise: Exercise
    user_id: UUID4
    verdict: Verdict
    submitted_at: datetime = Field(default_factory=lambda: datetime.now())
