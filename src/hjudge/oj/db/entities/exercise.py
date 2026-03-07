from typing import override

from sqlalchemy.orm import Mapped

from hjudge.commons.db.entities import BaseEntity
from hjudge.oj.models.judges import Exercise, JudgeEnum


class ExerciseEntity(BaseEntity):
    __tablename__ = "Exercise"
    judge: Mapped[JudgeEnum]
    code: Mapped[str]
    title: Mapped[str]

    @override
    def as_model(self) -> Exercise:
        return Exercise(
            id=self.id, judge=self.judge, code=self.code, title=self.title
        )
