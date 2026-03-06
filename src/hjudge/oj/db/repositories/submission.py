from typing import List, override
from uuid import UUID

from hjudge.commons.db import AbstractRepository, SQLAlchemyAbstractRepository
from hjudge.oj.models.submission import Submission


class AbstractSubmissionRepository(AbstractRepository):
    def add_submission(self, submission: Submission):
        raise NotImplementedError

    def get_submission(self, id: UUID) -> Submission | None:
        raise NotImplementedError

    def get_submissions_by_user_and_problem(
        self, user_id: UUID, exercise_id: UUID
    ) -> List[Submission]:
        raise NotImplementedError


class SQLAlchemySubmissionRepository(
    SQLAlchemyAbstractRepository, AbstractSubmissionRepository
):
    @override
    def add_submission(self, submission: Submission):
        self.session.add(submission)

    @override
    def get_submission(self, id: UUID) -> Submission | None:
        return self.session.query(Submission).filter_by(id=id).one_or_none()

    @override
    def get_submissions_by_user_and_problem(
        self, user_id: UUID, exercise_id: UUID
    ) -> List[Submission]:
        return (
            self.session.query(Submission)
            .filter_by(user_id=user_id, exercise_id=exercise_id)
            .all()
        )