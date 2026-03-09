from typing import List, override
from uuid import UUID

from hjudge.commons.db.repositories import AbstractRepository, SQLAlchemyAbstractRepository
from hjudge.oj.db.entities.submission import SubmissionEntity


class AbstractSubmissionRepository(AbstractRepository):
    def get_submission(self, id: UUID) -> SubmissionEntity | None:
        raise NotImplementedError

    def add_submission(self, entity: SubmissionEntity):
        raise NotImplementedError

    def get_submissions_by_exercise_and_user(
        self, exercise_id: UUID, user_id: UUID
    ) -> List[SubmissionEntity]:
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
    def get_submissions_by_exercise_and_user(
        self, exercise_id: UUID, user_id: UUID
    ) -> List[SubmissionEntity]:
        return (
            self.session.query(SubmissionEntity)
            .filter_by(exercise_id=exercise_id, user=user_id)
            .all()
        )
