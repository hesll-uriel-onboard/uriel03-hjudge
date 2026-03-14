from typing import Type

from hjudge.oj.models.judges import (
    AbstractCrawler,
    AbstractJudge,
    DefaultCrawler,
    JudgeEnum,
)
from hjudge.oj.models.judges.codeforces import CodeforcesJudge


class JudgeFactory:
    __enum_to_judge__: dict[JudgeEnum, Type[AbstractJudge]] = {
        JudgeEnum.CODEFORCES: CodeforcesJudge
    }
    __judges_dict__: dict[JudgeEnum, AbstractJudge] = {}
    crawler: AbstractCrawler

    def __init__(self, crawler: AbstractCrawler) -> None:
        self.crawler = crawler

    def create_from(self, judge: JudgeEnum):
        result = self.__judges_dict__.get(
            judge, self.__enum_to_judge__[judge](self.crawler)
        )
        self.__judges_dict__[judge] = result
        return result


DEFAULT_JUDGE_FACTORY = JudgeFactory(DefaultCrawler())
