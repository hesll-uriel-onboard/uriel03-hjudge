from datetime import datetime
from uuid import UUID

from hjudge.commons.db.repositories import (
    AbstractRepository,
    SQLAlchemyAbstractRepository,
)
from hjudge.oj.db.entities.user_judge import UserJudgeEntity
from hjudge.oj.models.judges import JudgeEnum


class AbstractUserJudgeRepository(AbstractRepository):
    """A repository to manage UserJudge entries."""

    def get_by_user_and_judge(
        self, user_id: UUID, judge: JudgeEnum
    ) -> UserJudgeEntity | None:
        raise NotImplementedError

    def list_by_user(self, user_id: UUID) -> list[UserJudgeEntity]:
        raise NotImplementedError

    def list_all(self) -> list[UserJudgeEntity]:
        raise NotImplementedError

    def upsert(self, user_judge: UserJudgeEntity) -> None:
        """Create or update a UserJudge entry."""
        raise NotImplementedError

    def update_last_crawled(self, user_judge_id: UUID, timestamp: datetime) -> None:
        raise NotImplementedError


class SQLAlchemyUserJudgeRepository(
    SQLAlchemyAbstractRepository, AbstractUserJudgeRepository
):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get_by_user_and_judge(
        self, user_id: UUID, judge: JudgeEnum
    ) -> UserJudgeEntity | None:
        return (
            self.session.query(UserJudgeEntity)
            .filter_by(user_id=user_id, judge=judge)
            .one_or_none()
        )

    def list_by_user(self, user_id: UUID) -> list[UserJudgeEntity]:
        return self.session.query(UserJudgeEntity).filter_by(user_id=user_id).all()

    def list_all(self) -> list[UserJudgeEntity]:
        return self.session.query(UserJudgeEntity).all()

    def upsert(self, user_judge: UserJudgeEntity) -> None:
        existing = self.get_by_user_and_judge(user_judge.user_id, user_judge.judge)
        if existing is not None:
            existing.handle = user_judge.handle
            # Don't reset last_crawled - preserve it
        else:
            self.session.add(user_judge)

    def update_last_crawled(self, user_judge_id: UUID, timestamp: datetime) -> None:
        self.session.query(UserJudgeEntity).filter_by(id=user_judge_id).update(
            {"last_crawled": timestamp}
        )