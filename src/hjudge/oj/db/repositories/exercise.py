from typing import List, override
from uuid import UUID

from sqlalchemy import and_, func, or_

from hjudge.commons.db.repositories import (
    AbstractRepository,
    SQLAlchemyAbstractRepository,
)
from hjudge.oj.db.entities.exercise import ExerciseEntity
from hjudge.oj.models.judges import JudgeEnum


class AbstractExerciseRepository(AbstractRepository):
    def get_exercise(self, id: UUID) -> ExerciseEntity | None:
        raise NotImplementedError

    def get_exercises(
        self, page: int | None = None, per_page: int = 20
    ) -> tuple[List[ExerciseEntity], int]:
        """Get exercises with optional pagination.

        Args:
            page: Page number (1-indexed). If None, returns all exercises.
            per_page: Number of exercises per page.

        Returns:
            Tuple of (exercises list, total count)
        """
        raise NotImplementedError

    def get_exercise_by_judge_and_code(
        self, judge: JudgeEnum, code: str
    ) -> ExerciseEntity | None:
        raise NotImplementedError

    def add_exercise(self, exercise: ExerciseEntity):
        raise NotImplementedError

    def add_exercises(self, exercises: List[ExerciseEntity]):
        """Add new exercises from list of exercises.

        If an exercise in the exercises (identify by its judge and code)
        already exists, it will be ignored.
        """
        raise NotImplementedError


class SQLAlchemyExerciseRepostory(
    SQLAlchemyAbstractRepository, AbstractExerciseRepository
):
    @override
    def get_exercise(self, id: UUID) -> ExerciseEntity | None:
        return self.session.query(ExerciseEntity).filter_by(id=id).one_or_none()

    @override
    def get_exercises(
        self, page: int | None = None, per_page: int = 20
    ) -> tuple[List[ExerciseEntity], int]:
        query = self.session.query(ExerciseEntity)
        total = query.count()

        if page is not None:
            offset = (page - 1) * per_page
            query = query.offset(offset).limit(per_page)

        return query.all(), total

    @override
    def get_exercise_by_judge_and_code(
        self, judge: JudgeEnum, code: str
    ) -> ExerciseEntity | None:
        return (
            self.session.query(ExerciseEntity)
            .filter_by(judge=judge, code=code)
            .one_or_none()
        )

    @override
    def add_exercise(self, exercise: ExerciseEntity):
        return self.session.add(exercise)

    @override
    def add_exercises(self, exercises: List[ExerciseEntity]):
        result = (
            self.session.query(ExerciseEntity)
            .filter(
                or_(
                    *[
                        and_(
                            ExerciseEntity.judge == obj.judge,
                            ExerciseEntity.code == obj.code,
                        )
                        for obj in exercises
                    ]
                )
            )
            .all()
        )
        existed_exercises: set[tuple[JudgeEnum, str]] = set(
            [(obj.judge, obj.code) for obj in result]
        )

        new_exercises = []
        for exercise in exercises:
            if (exercise.judge, exercise.code) not in existed_exercises:
                new_exercises.append(exercise)

        return self.session.add_all(new_exercises)
