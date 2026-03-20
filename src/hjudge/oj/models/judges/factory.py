from typing import Type

from hjudge.oj.models.judges import (
    AbstractCrawler,
    AbstractJudge,
    DefaultCrawler,
    JudgeEnum,
)
from hjudge.oj.models.judges.atcoder import AtcoderJudge
from hjudge.oj.models.judges.codeforces import CodeforcesJudge
from hjudge.oj.models.judges.dmoj import DmojJudge
from hjudge.oj.models.judges.qoj import QojJudge


class JudgeFactory:
    __enum_to_judge__: dict[JudgeEnum, Type[AbstractJudge]] = {
        JudgeEnum.CODEFORCES: CodeforcesJudge,
        JudgeEnum.DMOJ: DmojJudge,
        JudgeEnum.ATCODER: AtcoderJudge,
        JudgeEnum.QOJ: QojJudge,
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
