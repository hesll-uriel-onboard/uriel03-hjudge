from typing import Type

from hjudge.oj.models.judges import AbstractJudge, JudgeEnum
from hjudge.oj.models.judges.codeforces import CodeforcesJudge


class JudgeFactory:
    __enum_to_judge__: dict[JudgeEnum, Type[AbstractJudge]] = {
        JudgeEnum.CODEFORCES: CodeforcesJudge
    }
    __judges__: dict[JudgeEnum, AbstractJudge] = {}

    @staticmethod
    def create_from(judge: JudgeEnum):
        result = JudgeFactory.__judges__.get(
            judge, JudgeFactory.__enum_to_judge__[judge]()
        )
        JudgeFactory.__judges__[judge] = result
        return result
