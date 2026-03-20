from typing import List, override
from uuid import UUID

from sqlalchemy import func

from hjudge.commons.db.repositories import (
    AbstractRepository,
    SQLAlchemyAbstractRepository,
)
from hjudge.oj.db.entities.submission import SubmissionEntity
from hjudge.oj.models.judges import JudgeEnum


class AbstractSubmissionRepository(AbstractRepository):
    def get_submission(self, id: UUID) -> SubmissionEntity | None:
        raise NotImplementedError

    def get_by_submission_id_and_judge(
        self, submission_id: str, judge: JudgeEnum
    ) -> SubmissionEntity | None:
        raise NotImplementedError

    def add_submission(self, entity: SubmissionEntity):
        raise NotImplementedError

    def add_submissions_batch(
        self, entities: List[SubmissionEntity]
    ) -> List[SubmissionEntity]:
        """Insert multiple submissions, skipping duplicates by (submission_id, judge).
        Returns only the entities that were successfully inserted.
        """
        raise NotImplementedError

    def get_submissions_by_exercise_and_user(
        self, exercise_id: UUID, user_id: UUID
    ) -> List[SubmissionEntity]:
        raise NotImplementedError

    def get_max_points_by_exercise_and_user(
        self,
        exercise_ids: List[UUID],
        user_ids: List[UUID] | None = None,
    ) -> dict[tuple[UUID, UUID], int]:
        """Get max points per (exercise_id, user_id) pair.

        Args:
            exercise_ids: List of exercise IDs to query
            user_ids: Optional list of user IDs to filter. If None, returns all users.

        Returns:
            Dict mapping (exercise_id, user_id) -> max_points
        """
        raise NotImplementedError


class SQLAlchemySubmissionRepository(
    SQLAlchemyAbstractRepository, AbstractSubmissionRepository
):
    @override
    def add_submission(self, entity: SubmissionEntity):
        return self.session.add(entity)

    @override
    def get_submission(self, id: UUID) -> SubmissionEntity | None:
        return (
            self.session.query(SubmissionEntity).filter_by(id=id).one_or_none()
        )

    @override
    def get_by_submission_id_and_judge(
        self, submission_id: str, judge: JudgeEnum
    ) -> SubmissionEntity | None:
        from hjudge.oj.db.entities.exercise import ExerciseEntity

        return (
            self.session.query(SubmissionEntity)
            .join(ExerciseEntity)
            .filter(SubmissionEntity.submission_id == submission_id)
            .filter(ExerciseEntity.judge == judge)
            .one_or_none()
        )

    @override
    def add_submissions_batch(
        self, entities: List[SubmissionEntity]
    ) -> List[SubmissionEntity]:
        """Insert multiple submissions, skipping duplicates by (submission_id, judge).
        Returns only the entities that were successfully inserted.
        """
        if not entities:
            return []

        from hjudge.oj.db.entities.exercise import ExerciseEntity

        # Get all existing (submission_id, judge) pairs
        submission_ids = [e.submission_id for e in entities]
        existing = (
            self.session.query(SubmissionEntity.submission_id, ExerciseEntity.judge)
            .join(ExerciseEntity)
            .filter(SubmissionEntity.submission_id.in_(submission_ids))
            .all()
        )
        existing_pairs = {(row[0], row[1]) for row in existing}

        # Filter out duplicates - need to check via exercise relationship
        # We need to load exercises for comparison
        new_entities = []
        for e in entities:
            # Get the exercise's judge from the entity's exercise relationship
            # The exercise should be loaded before calling this method
            if not hasattr(e, '_exercise_judge'):
                # Query the exercise to get judge
                exercise = self.session.query(ExerciseEntity).filter_by(id=e.exercise_id).first()
                if exercise:
                    pair = (e.submission_id, exercise.judge)
                    if pair not in existing_pairs:
                        new_entities.append(e)
            else:
                pair = (e.submission_id, e._exercise_judge)
                if pair not in existing_pairs:
                    new_entities.append(e)

        if new_entities:
            self.session.add_all(new_entities)

        return new_entities

    @override
    def get_submissions_by_exercise_and_user(
        self, exercise_id: UUID, user_id: UUID
    ) -> List[SubmissionEntity]:
        return (
            self.session.query(SubmissionEntity)
            .filter_by(exercise_id=exercise_id, user_id=user_id)
            .order_by(SubmissionEntity.submitted_at.desc())
            .all()
        )

    @override
    def get_max_points_by_exercise_and_user(
        self,
        exercise_ids: List[UUID],
        user_ids: List[UUID] | None = None,
    ) -> dict[tuple[UUID, UUID], int]:
        """Get max points per (exercise_id, user_id) pair."""
        if not exercise_ids:
            return {}

        # Build query: SELECT exercise_id, user_id, MAX(points) GROUP BY exercise_id, user_id
        query = (
            self.session.query(
                SubmissionEntity.exercise_id,
                SubmissionEntity.user_id,
                func.max(SubmissionEntity.points).label("max_points"),
            )
            .filter(SubmissionEntity.exercise_id.in_(exercise_ids))
            .group_by(SubmissionEntity.exercise_id, SubmissionEntity.user_id)
        )

        if user_ids is not None:
            query = query.filter(SubmissionEntity.user_id.in_(user_ids))

        results = query.all()

        return {(row.exercise_id, row.user_id): row.max_points for row in results}
