from datetime import datetime
from typing import override
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hjudge.commons.db.entities import BaseEntity
from hjudge.oj.db.entities.exercise import ExerciseEntity
from hjudge.oj.models.submission import Submission, Verdict


class SubmissionEntity(BaseEntity):
    __tablename__ = "Submission"
    exercise_id: Mapped[UUID] = mapped_column(ForeignKey("Exercise.id"))
    exercise: Mapped["ExerciseEntity"] = relationship(init=False)
    user_id: Mapped[UUID]
    verdict: Mapped["Verdict"]
    submission_id: Mapped[str]
    submitted_at: Mapped[datetime]
    content: Mapped[str] = mapped_column(default="")

    @override
    def as_model(self, **kwargs) -> Submission:
        return Submission(
            id=self.id,
            exercise=self.exercise.as_model(),
            user_id=self.user_id,
            verdict=self.verdict,
            submission_id=self.submission_id,
            submitted_at=self.submitted_at,
            content=self.content,
        )