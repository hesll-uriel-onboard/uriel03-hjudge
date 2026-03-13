import string
from datetime import datetime, timezone
from json import JSONDecoder
from typing import Any, ClassVar, Iterable, List, Self, override

from hjudge.commons.endpoints.status_codes import HTTP_200_OK
from hjudge.oj.errors import (
    CodeforcesContestNotFoundError,
    ExerciseNotFoundError,
)
from hjudge.oj.models.judges import (
    AbstractJudge,
    Exercise,
    JudgeEnum,
    UserJudge,
)
from hjudge.oj.models.submission import Submission, Verdict

# Mapping from Codeforces verdicts to our Verdict enum
CF_VERDICT_MAP = {
    "OK": Verdict.AC,
    "WRONG_ANSWER": Verdict.WA,
    "TIME_LIMIT_EXCEEDED": Verdict.TLE,
    "MEMORY_LIMIT_EXCEEDED": Verdict.RTE,
    "RUNTIME_ERROR": Verdict.RTE,
    "COMPILATION_ERROR": Verdict.RTE,
    "CHALLENGED": Verdict.WA,
    "SKIPPED": Verdict.WA,
    "TESTING": None,  # Still being judged
    "REJECTED": None,  # Rejected by judge
}


class CodeforcesExercise(Exercise):
    CONTEST_ID: ClassVar = "contestId"
    INDEX: ClassVar = "index"
    NAME: ClassVar = "name"

    def __init__(self, code: str, title: str):
        code = code.upper()
        super().__init__(judge=JudgeEnum.CODEFORCES, code=code, title=title)
        # self.contest, self.problem = CodeforcesExercise.parse(self.code)

    @staticmethod
    def parse(code: str) -> tuple[str, str]:
        ans = -1
        for i, c in enumerate(code):
            if c in string.ascii_letters:
                ans = i
                break
        if ans == -1:
            raise ExerciseNotFoundError
        return (code[:ans], code[ans:])

    @override
    @classmethod
    def create_from(cls, data: dict, *args, **kwargs) -> Self:
        contest_id = data[CodeforcesExercise.CONTEST_ID]
        index = data[CodeforcesExercise.INDEX]
        title = data[CodeforcesExercise.NAME]
        return cls(f"{contest_id}{index}", title)


class CodeforcesJudge(AbstractJudge):
    __cached: dict[str, List[Exercise]] = {}

    @property
    def cached(self) -> dict[str, List[Exercise]]:
        return CodeforcesJudge.__cached

    @override
    def get_batch_config(self, from_exercise: str) -> dict[str, Any]:
        contest, _ = CodeforcesExercise.parse(from_exercise)
        return {
            "contest": contest,
            "url": f"https://codeforces.com/api/contest.standings?contestId={contest}",
        }

    @override
    def get_exercise_url(self, code: str) -> str:
        contest, problem = CodeforcesExercise.parse(code)
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
            response = self.crawler.get(url)
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

    @override
    def get_submission_url(
        self, submission_id: str, code: str, *args, **kwargs
    ) -> str:
        """Get the URL to view a Codeforces submission.

        Args:
            code: The exercise code (e.g., "1234A")
            submission_id: The submission ID from Codeforces
        """
        contest, _ = CodeforcesExercise.parse(code)
        return f"https://codeforces.com/contest/{contest}/submission/{submission_id}"

    @override
    def crawl_user_submissions(
        self, user_judge: UserJudge, from_timestamp: datetime
    ) -> list[Submission]:
        """Crawl submissions for a Codeforces user after the given timestamp.

        Uses the Codeforces API: https://codeforces.com/api/user.status
        """
        url = f"https://codeforces.com/api/user.status?handle={user_judge.handle}"

        try:
            response = self.crawler.get(url)
            if response.status_code != HTTP_200_OK:
                return []

            data = JSONDecoder().decode(response.content.decode())
            if data.get("status") != "OK":
                return []

            submissions_data: list[dict] = data.get("result", [])
            submissions = []

            for sub_data in submissions_data:
                # Get submission time
                time_seconds = sub_data.get("creationTimeSeconds", 0)
                submitted_at = datetime.fromtimestamp(
                    time_seconds, tz=timezone.utc
                )

                # Skip if before from_timestamp
                if submitted_at <= from_timestamp:
                    continue

                # Get verdict
                cf_verdict = sub_data.get("verdict", "")
                verdict = CF_VERDICT_MAP.get(cf_verdict)
                if verdict is None:
                    continue  # Skip submissions without a valid verdict

                # Get problem info
                problem = sub_data.get("problem", {})
                contest_id = problem.get("contestId")
                index = problem.get("index", "")

                if contest_id is None or not index:
                    continue

                code = f"{contest_id}{index}"
                title = problem.get("name", "")

                # Create exercise
                exercise = Exercise(
                    judge=JudgeEnum.CODEFORCES,
                    code=code,
                    title=title,
                )

                # Create submission with user_id from UserJudge
                submission = Submission(
                    exercise=exercise,
                    user_id=user_judge.user_id,
                    verdict=verdict,
                    submission_id=str(sub_data.get("id", "")),
                    submitted_at=submitted_at,
                    content="",  # Codeforces API doesn't provide code in this endpoint
                )
                submissions.append(submission)

            return submissions

        except Exception:
            return []
