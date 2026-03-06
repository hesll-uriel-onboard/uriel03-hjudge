from abc import ABC
from enum import Enum
from typing import override

from sqlalchemy.orm import Mapped

from hjudge.commons.models import Base
from hjudge.oj.errors import JudgeNotExistedError

################## data classes ##################


class JudgeEnum(Enum):
    CODEFORCES = "Codeforces"
    ATCODER = "AtCoder"
    VNOJ = "VNOJ"


class Exercise(Base):
    __tablename__ = "Exercise"
    judge: Mapped[JudgeEnum]
    code: Mapped[str]
    title: Mapped[str]
    


################## implementing judges ##################


class AbstractJudge(ABC):
    def exercise_url(self, id: str) -> str:
        raise NotImplementedError

    def parse(self, html: str) -> dict:
        raise NotImplementedError


class CodeforcesJudge(AbstractJudge):
    @override
    def exercise_url(self, id: str) -> str:
        contest, problem = id[:-1], id[-1]
        return f"https://codeforces.com/problemset/problem/{contest}/{problem}"

    @override
    def parse(self, html: str) -> dict:
        return super().parse(html)


def create_judge(judge: JudgeEnum) -> AbstractJudge:
    if judge == JudgeEnum.CODEFORCES:
        return CodeforcesJudge()
    raise JudgeNotExistedError
