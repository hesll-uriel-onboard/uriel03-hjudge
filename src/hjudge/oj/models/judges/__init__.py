import abc
from datetime import datetime
from enum import StrEnum
from typing import Any, Iterable, Protocol, Self

import requests

from hjudge.commons.models import Base

################## data classes ##################


class JudgeEnum(StrEnum):
    CODEFORCES = "CODEFORCES"
    DMOJ = "DMOJ"
    ATCODER = "ATCODER"
    QOJ = "QOJ"


class Exercise(Base):
    judge: JudgeEnum
    code: str
    title: str = ""

    @classmethod
    def create_from(cls, *args, **kwargs) -> Self:
        raise NotImplementedError


####### crawler class, for testing purpose, totally unnecessary #######
class AbstractCrawler(abc.ABC):
    """An interface that duplicate requests.get

    For testing purpose, the request class
    """

    @abc.abstractmethod
    def get(self, url: str, *args, **kwargs):
        raise NotImplementedError


class DefaultCrawler(AbstractCrawler):
    def get(self, url: str, *args, **kwargs):
        return requests.get(url=url, *args, **kwargs)


class AbstractJudge(Protocol):
    """An abstract interface of OJ's problem manager

    Each judges shall have a mechanism to cached. This cached
    shall be global, i.e. a static property of the OJ's class.
    """

    crawler: AbstractCrawler

    def __init__(self, crawler: AbstractCrawler):
        self.crawler = crawler

    @abc.abstractmethod
    def get_exercise_url(self, code: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_batch_config(self, from_exercise: str) -> dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def crawl_exercises_batch(self, url: str, *args, **kwargs) -> Iterable[Exercise]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_submission_url(self, submission_id: str, **kwargs) -> str:
        """Get the URL to view a submission on the judge's website.

        Args:
            submission_id: The submission ID from the judge
            **kwargs: Additional parameters (e.g., code for contest ID)
        """
        raise NotImplementedError

    @abc.abstractmethod
    def crawl_user_submissions(
        self, user_judge: "UserJudge", from_timestamp: datetime
    ) -> list["Submission"]:
        """Crawl submissions for a user after the given timestamp.

        Args:
            user_judge: The UserJudge record containing user_id, judge, and handle
            from_timestamp: Only return submissions after this time

        Returns:
            List of Submission objects with user_id set from user_judge
        """
        raise NotImplementedError


# Import here to avoid circular import
from hjudge.oj.models.submission import Submission
from hjudge.oj.models.user_judge import UserJudge
