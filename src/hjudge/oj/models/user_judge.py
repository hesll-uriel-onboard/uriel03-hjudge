from datetime import datetime, timezone
from uuid import UUID

from pydantic import Field

from hjudge.commons.models import Base
from hjudge.oj.models.judges import JudgeEnum


class UserJudge(Base):
    """Represents a user's handle on an Online Judge"""

    user_id: UUID
    judge: JudgeEnum
    handle: str
    last_crawled: datetime = Field(
        default_factory=lambda: datetime.fromtimestamp(0, tz=timezone.utc)
    )