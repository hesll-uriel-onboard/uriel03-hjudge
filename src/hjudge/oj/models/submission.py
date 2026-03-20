from datetime import datetime
from enum import Enum

from pydantic import UUID4, Field

from hjudge.commons.models import Base
from hjudge.oj.models.judges import Exercise


class Verdict(Enum):
    AC = "AC"
    WA = "WA"
    TLE = "TLE"
    RTE = "RTE"
    CE = "CE"
    IE = "IE"


class Submission(Base):
    exercise: Exercise
    user_id: UUID4
    verdict: Verdict
    submission_id: str
    submitted_at: datetime = Field(default_factory=lambda: datetime.now())
    content: str = ""
    points: int = 0
