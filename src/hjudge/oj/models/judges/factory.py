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
from hjudge.oj.models.judges.lqdoj import LqdojJudge
from hjudge.oj.models.judges.qoj import QojJudge


class JudgeFactory:
    __enum_to_judge__: dict[JudgeEnum, Type[AbstractJudge]] = {
        JudgeEnum.CODEFORCES: CodeforcesJudge,
        JudgeEnum.DMOJ: DmojJudge,
        JudgeEnum.ATCODER: AtcoderJudge,
        JudgeEnum.QOJ: QojJudge,
        JudgeEnum.LQDOJ: LqdojJudge,
    }
    crawler: AbstractCrawler

    def __init__(self, crawler: AbstractCrawler) -> None:
        self.crawler = crawler

    def create_from(self, judge: JudgeEnum) -> AbstractJudge:
        """Create a fresh judge instance.

        Note: Each call returns a fresh instance since judges are now
        async context managers with their own browser lifecycle.
        """
        return self.__enum_to_judge__[judge](self.crawler)


DEFAULT_JUDGE_FACTORY = JudgeFactory(DefaultCrawler())
