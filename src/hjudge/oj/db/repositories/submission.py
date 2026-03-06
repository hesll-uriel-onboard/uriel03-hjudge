from typing import List
from uuid import UUID

from hjudge.commons.db.repositories import AbstractRepository
from hjudge.oj.db.entities.submission import SubmissionEntity


class AbstractSubmissionRepository(AbstractRepository):
    def get_submission(self, id: UUID) -> SubmissionEntity:
        raise NotImplementedError

    def add_submission(self, user: SubmissionEntity):
        raise NotImplementedError

    def get_submission_by_user(self, user_id: UUID) -> List[SubmissionEntity]:
        raise NotImplementedError
