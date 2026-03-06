from typing import override
from uuid import UUID

from hjudge.commons.db import AbstractRepository, SQLAlchemyAbstractRepository
from hjudge.oj.models.judge import Exercise


class AbstractExerciseRepository(AbstractRepository):
    def get_exercise(self, id: UUID) -> Exercise | None:
        raise NotImplementedError

    def add_exercise(self, exercise: Exercise):
        raise NotImplementedError

    # TODO: update_exercise after a while


class SQLAlchemyExerciseRepository(
    AbstractExerciseRepository, SQLAlchemyAbstractRepository
):
    @override
    def get_exercise(self, id: UUID) -> Exercise | None:
        return self.session.query(Exercise).filter_by(id=id).one_or_none()

    @override
    def add_exercise(self, exercise: Exercise):
        self.session.add(exercise)
