import string
from datetime import datetime, timezone
from typing import Any, ClassVar, Iterable, List, Self, override

from bs4 import BeautifulSoup

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
    "Accepted": Verdict.AC,
    "Wrong answer": Verdict.WA,
    "Time limit exceeded": Verdict.TLE,
    "Memory limit exceeded": Verdict.RTE,
    "Runtime error": Verdict.RTE,
    "Compilation error": Verdict.CE,
    "Challenged": Verdict.WA,
    "Skipped": Verdict.WA,
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

    @override
    def get_batch_config(self, from_exercise: str) -> dict[str, Any]:
        contest, _ = CodeforcesExercise.parse(from_exercise)
        return {
            "contest": contest,
            "url": f"{BASE_URL}/contest/{contest}",
        }

    @override
    def get_exercise_url(self, code: str) -> str:
        contest, problem = CodeforcesExercise.parse(code)
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
            return f"{BASE_URL}/contest/{contest}/submission/{submission_id}"
        return f"{BASE_URL}/submissions/{submission_id}"

    @override
    async def crawl_user_submissions(
        self, user_judge: UserJudge, from_timestamp: datetime
    ) -> list[Submission]:
        if self._browser is None:
            raise RuntimeError("Browser not initialized. Use async context manager.")

        submissions = []
        page = 1

        while True:
            url = f"{BASE_URL}/submissions/{user_judge.handle}/page/{page}"
            try:
                html = await self._browser.get_page_content(url, wait_for="table.status-frame-datatable")
            except Exception:
                break

            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", class_="status-frame-datatable")
            if not table:
                break

            rows = table.find_all("tr")[1:]
            if not rows:
                break

            found_old = False
            for row in rows:
                try:
                    cols = row.find_all("td")
                    if len(cols) < 6:
                        continue

                    submission_id = cols[0].get_text(strip=True)

                    time_el = cols[1].find("span", attrs={"data-timestamp": True})
                    if not time_el:
                        continue
                    ts = int(time_el["data-timestamp"])
                    submitted_at = datetime.fromtimestamp(ts, tz=timezone.utc)

                    if submitted_at <= from_timestamp:
                        found_old = True
                        continue

                    problem_link = cols[3].find("a")
                    if not problem_link:
                        continue
                    problem_title = problem_link.get_text(strip=True)
                    href = problem_link.get("href", "")
                    # href like /contest/1234/problem/A
                    parts = href.strip("/").split("/")
                    if len(parts) >= 4:
                        contest_id = parts[1]
                        index = parts[3]
                        code = f"{contest_id}{index}"
                    else:
                        continue

                    verdict_el = cols[5]
                    verdict_text = verdict_el.get_text(strip=True)
                    verdict = next(
                        (v for k, v in CF_VERDICT_MAP.items() if verdict_text.startswith(k)),
                        None,
                    )
                    if verdict is None:
                        continue

                    exercise = Exercise(judge=JudgeEnum.CODEFORCES, code=code, title=problem_title)
                    submissions.append(Submission(
                        exercise=exercise,
                        user_id=user_judge.user_id,
                        verdict=verdict,
                        submission_id=submission_id,
                        submitted_at=submitted_at,
                        content="",
                        points=100 if verdict == Verdict.AC else 0,
                    ))
                except Exception:
                    continue

            if found_old or len(rows) < 50:
                break

            page += 1

        return submissions
