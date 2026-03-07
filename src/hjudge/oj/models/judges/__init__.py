import abc
from enum import Enum, StrEnum
from json import JSONDecoder
from typing import Any, Iterable, List, Protocol, Self, override
from xml.etree import ElementTree as etree

from hjudge.commons.endpoints.status_codes import HTTP_200_OK
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


class AbstractJudge(Protocol):
    @abc.abstractmethod
    def get_exercise_url(self, id: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_batch_config(self, from_exercise: str) -> dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def crawl_exercises_batch(self, url: str, **kwargs) -> Iterable[Exercise]:
        raise NotImplementedError
