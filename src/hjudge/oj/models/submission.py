from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing_extensions import deprecated

from hjudge.commons.models import Base
from hjudge.oj.models.judge import Exercise, JudgeEnum


class Verdict(Enum):
    AC = "Accepted"
    WA = "Wrong Answer"
    TLE = "Time Limit Exceeded"
    RTE = "Run-Time Error"


@deprecated("Will be use eventually")
class UserJudge(Base):
    __tablename__ = "UserJudge"
    user_id: Mapped[UUID]
    judge: Mapped[JudgeEnum]
    handle: Mapped[str]


class Submission(Base):
    __tablename__ = "Submission"
    exercise_id: Mapped[UUID] = mapped_column(ForeignKey("Exercise.id"))
    exercise: Mapped[Exercise] = relationship(
        "Exercise", #back_populates="Submission"
    )
    user: Mapped[UUID]
    verdict: Mapped["Verdict"]
    submitted_at: Mapped[datetime] = mapped_column(
        default_factory=lambda: datetime.now()
    )
