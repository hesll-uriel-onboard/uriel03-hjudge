import string
from datetime import datetime, timezone
from json import JSONDecoder
from typing import Any, ClassVar, Iterable, List, Self, override

from bs4 import BeautifulSoup

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
from hjudge.oj.services.browser import FlareSolverrCrawler

CF_VERDICT_MAP = {
    "OK": Verdict.AC,
    "WRONG_ANSWER": Verdict.WA,
    "TIME_LIMIT_EXCEEDED": Verdict.TLE,
    "MEMORY_LIMIT_EXCEEDED": Verdict.RTE,
    "RUNTIME_ERROR": Verdict.RTE,
    "COMPILATION_ERROR": Verdict.CE,
    "CHALLENGED": Verdict.WA,
    "SKIPPED": Verdict.WA,
}

BASE_URL = "https://codeforces.com"


class CodeforcesExercise(Exercise):
    CONTEST_ID: ClassVar = "contestId"
    INDEX: ClassVar = "index"
    NAME: ClassVar = "name"

    def __init__(self, code: str, title: str):
        code = code.upper()
        super().__init__(judge=JudgeEnum.CODEFORCES, code=code, title=title)

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
    _browser: FlareSolverrCrawler | None = None

    @property
    def cached(self) -> dict[str, List[Exercise]]:
        return CodeforcesJudge.__cached

    async def __aenter__(self) -> Self:
        self._browser = FlareSolverrCrawler()
        await self._browser.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._browser:
            await self._browser.__aexit__(exc_type, exc_val, exc_tb)

    @staticmethod
    def _is_gym(contest_id: str) -> bool:
        return len(contest_id) == 6

    @override
    def get_batch_config(self, from_exercise: str) -> dict[str, Any]:
        contest, _ = CodeforcesExercise.parse(from_exercise)
        section = "gym" if self._is_gym(contest) else "contest"
        return {
            "contest": contest,
            "url": f"{BASE_URL}/{section}/{contest}",
        }

    @override
    def get_exercise_url(self, code: str) -> str:
        contest, problem = CodeforcesExercise.parse(code)
        if self._is_gym(contest):
            return f"{BASE_URL}/gym/{contest}/problem/{problem}"
        return f"{BASE_URL}/problemset/problem/{contest}/{problem}"

    @override
    async def crawl_exercises_batch(self, url: str, **kwargs) -> Iterable[Exercise]:
        contest_id = str(kwargs.get("contest", ""))
        if not contest_id:
            raise CodeforcesContestNotFoundError

        cached = self.cached.get(contest_id)
        if cached is not None:
            return cached

        if self._browser is None:
            raise RuntimeError("Browser not initialized. Use async context manager.")

        try:
            html = await self._browser.get_page_content(url, wait_for="table.problems")
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", class_="problems")
            if not table:
                raise ExerciseNotFoundError

            result = []
            for row in table.find_all("tr")[1:]:  # skip header
                cols = row.find_all("td")
                if len(cols) < 2:
                    continue
                index = cols[0].get_text(strip=True)
                title = cols[1].find("a")
                if not title:
                    continue
                title = title.get_text(strip=True)
                result.append(CodeforcesExercise(f"{contest_id}{index}", title))

            self.cached[contest_id] = result
            return result
        except Exception:
            raise ExerciseNotFoundError

    @override
    def get_submission_url(self, submission_id: str, code: str = "", *args, **kwargs) -> str:
        if code:
            contest, _ = CodeforcesExercise.parse(code)
            section = "gym" if self._is_gym(contest) else "contest"
            return f"{BASE_URL}/{section}/{contest}/submission/{submission_id}"
        return f"{BASE_URL}/submissions/{submission_id}"

    @override
    async def crawl_user_submissions(
        self, user_judge: UserJudge, from_timestamp: datetime
    ) -> list[Submission]:
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
                time_seconds = sub_data.get("creationTimeSeconds", 0)
                submitted_at = datetime.fromtimestamp(time_seconds, tz=timezone.utc)

                if submitted_at <= from_timestamp:
                    continue

                cf_verdict = sub_data.get("verdict", "")
                verdict = CF_VERDICT_MAP.get(cf_verdict)
                if verdict is None:
                    continue

                points = sub_data.get("points")
                if points is None:
                    points = 100 if verdict == Verdict.AC else 0

                problem = sub_data.get("problem", {})
                contest_id = problem.get("contestId")
                index = problem.get("index", "")

                if contest_id is None or not index:
                    continue

                code = f"{contest_id}{index}"
                title = problem.get("name", "")

                exercise = Exercise(
                    judge=JudgeEnum.CODEFORCES,
                    code=code,
                    title=title,
                )
                submission = Submission(
                    exercise=exercise,
                    user_id=user_judge.user_id,
                    verdict=verdict,
                    submission_id=str(sub_data.get("id", "")),
                    submitted_at=submitted_at,
                    content="",
                    points=points,
                )
                submissions.append(submission)

            return submissions

        except Exception:
            return []
