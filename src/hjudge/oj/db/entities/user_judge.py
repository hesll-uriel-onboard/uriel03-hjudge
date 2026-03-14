from datetime import datetime
from typing import override
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import UniqueConstraint

from hjudge.commons.db.entities import BaseEntity
from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.user_judge import UserJudge


class UserJudgeEntity(BaseEntity):
    """Represents a user's handle on an Online Judge"""

    __tablename__ = "UserJudge"
    __table_args__ = (UniqueConstraint("user_id", "judge", name="uq_user_judge"),)

    user_id: Mapped[UUID]
    judge: Mapped[JudgeEnum]
    handle: Mapped[str]
    last_crawled: Mapped[datetime]

    @override
    def as_model(self, **kwargs) -> UserJudge:
        return UserJudge(
            id=self.id,
            user_id=self.user_id,
            judge=self.judge,
            handle=self.handle,
            last_crawled=self.last_crawled,
        )