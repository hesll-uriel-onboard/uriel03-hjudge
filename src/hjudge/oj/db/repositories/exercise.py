from typing import override
from uuid import UUID

from hjudge.commons.db.repositories import (
    AbstractRepository,
    SQLAlchemyAbstractRepository,
)
from hjudge.oj.db.entities.exercise import ExerciseEntity


class AbstractExerciseRepository(AbstractRepository):
    def get_exercise(self, id: UUID) -> ExerciseEntity | None:
        raise NotImplementedError

    def add_exercise(self, exercise: ExerciseEntity):
        raise NotImplementedError


class SQLAlchemyExerciseRepostory(
    SQLAlchemyAbstractRepository, AbstractExerciseRepository
):
    @override
    def get_exercise(self, id: UUID) -> ExerciseEntity | None:
        return self.session.query(ExerciseEntity).filter_by(id=id).one_or_none()

    @override
    def add_exercise(self, exercise: ExerciseEntity):
        return self.session.add(exercise)
