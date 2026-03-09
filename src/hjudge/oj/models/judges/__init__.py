import abc
from enum import StrEnum
from typing import Any, Iterable, Protocol, Self

import requests

from hjudge.commons.models import Base

################## data classes ##################


class JudgeEnum(StrEnum):
    CODEFORCES = "CodeForces"


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
    def get_exercise_url(self, id: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_batch_config(self, from_exercise: str) -> dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def crawl_exercises_batch(self, url: str, **kwargs) -> Iterable[Exercise]:
        raise NotImplementedError
