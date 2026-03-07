from json import JSONDecoder
from turtle import title
from typing import Any, ClassVar, Iterable, List, Self, override

import requests

from hjudge.commons.endpoints.status_codes import HTTP_200_OK
from hjudge.oj.errors import (
    CodeforcesContestNotFoundError,
    ExerciseNotFoundError,
)
from hjudge.oj.models.judges import AbstractJudge, Exercise, JudgeEnum


class CodeforcesExercise(Exercise):
    CONTEST_ID: ClassVar = "contestId"
    INDEX: ClassVar = "index"
    NAME: ClassVar = "name"

    def __init__(self, code: str, title: str):
        super().__init__(judge=JudgeEnum.CODEFORCES, code=code, title=title)

    @override
    @classmethod
    def create_from(cls, data: dict, *args, **kwargs) -> Self:
        contest_id = data[CodeforcesExercise.CONTEST_ID]
        index = data[CodeforcesExercise.INDEX]
        title = data[CodeforcesExercise.NAME]
        return cls(f"{contest_id}{index}", title)


class CodeforcesJudge(AbstractJudge):

    def __init__(self) -> None:
        self.cached: dict[str, List[Exercise]] = {}

    @override
    def get_batch_config(self, from_exercise: str) -> dict[str, Any]:
        contest = from_exercise[:-1]
        return {
            "contest": contest,
            "url": f"https://codeforces.com/api/contest.standings?contestId={contest}",
        }

    @override
    def get_exercise_url(self, id: str) -> str:
        contest, problem = id[:-1], id[-1]
        return f"https://codeforces.com/problemset/problem/{contest}/{problem}"

    @override
    def crawl_exercises_batch(self, url: str, **kwargs) -> Iterable[Exercise]:
        contest_id = kwargs.get("contest")
        if contest_id is None:
            raise CodeforcesContestNotFoundError
        contest_id = str(contest_id)

        result = self.cached.get(contest_id)
        if result is not None:
            return result

        result = []
        try:
            response = requests.get(url)
            if response.status_code != HTTP_200_OK:
                raise ExerciseNotFoundError

            problems_info: list[dict] = JSONDecoder().decode(
                response.content.decode()
            )["result"]["problems"]

            for problem_info in problems_info:
                exercise = CodeforcesExercise.create_from(data=problem_info)
                result.append(exercise)
        except Exception:
            raise ExerciseNotFoundError

        self.cached[contest_id] = result
        return result


# class CodeforcesJudge(AbstractJudge):
#     @override
#     def exercise_url(self, id: str) -> str:

#     @override
#     def parse(self, html: str) -> dict:
#         return super().parse(html)


# def create_judge(judge: JudgeEnum) -> AbstractJudge:
#     if judge == JudgeEnum.CODEFORCES:
#         return CodeforcesJudge()
#     raise JudgeNotExistedError
