import re
from datetime import datetime, timezone
from typing import Any, ClassVar, Iterable, List, Self, override

from bs4 import BeautifulSoup

from hjudge.oj.errors import AtcoderProblemNotFoundError, ExerciseNotFoundError
from hjudge.oj.models.judges import (
    AbstractCrawler,
    AbstractJudge,
    Exercise,
    JudgeEnum,
    UserJudge,
)
from hjudge.oj.models.submission import Submission, Verdict
from hjudge.oj.services.browser import FlareSolverrCrawler

# Mapping from AtCoder verdicts to our Verdict enum
ATCODER_VERDICT_MAP = {
    "AC": Verdict.AC,
    "WA": Verdict.WA,
    "TLE": Verdict.TLE,
    "RE": Verdict.RTE,  # Runtime Error
    "MLE": Verdict.RTE,  # Memory Limit Exceeded
    "OLE": Verdict.RTE,  # Output Limit Exceeded
    "CE": Verdict.CE,
    "IE": Verdict.IE,  # Internal Error
}


class AtcoderExercise(Exercise):
    """AtCoder exercise with contest_problem code format.

    Code format: {contest}_{problem} (e.g., abc360_a)
    """

    CONTEST: ClassVar = "contest"
    PROBLEM: ClassVar = "problem"

    def __init__(self, code: str, title: str = ""):
        super().__init__(judge=JudgeEnum.ATCODER, code=code.lower(), title=title)

    @property
    def contest(self) -> str:
        """Get contest name from code."""
        return self.parse(self.code)[0]

    @property
    def problem(self) -> str:
        """Get problem letter from code."""
        return self.parse(self.code)[1]

    @staticmethod
    def parse(code: str) -> tuple[str, str]:
        """Parse code like 'abc360_a' into ('abc360', 'a')"""
        parts = code.lower().split("_")
        if len(parts) != 2:
            raise ExerciseNotFoundError
        return (parts[0], parts[1])

    @override
    @classmethod
    def create_from(cls, data: dict, *args, **kwargs) -> Self:
        """Create AtcoderExercise from parsed data.

        Expected data format:
        {
            "contest": "abc360",
            "problem": "a",
            "name": "A - A Simple Problem"
        }
        """
        contest = data[AtcoderExercise.CONTEST]
        problem = data[AtcoderExercise.PROBLEM]
        name = data.get("name", "")
        return cls(f"{contest}_{problem}", name)


class AtcoderJudge(AbstractJudge):
    """AtCoder judge implementation using browser automation.

    AtCoder's unofficial API is currently Forbidden, so we use FlareSolverr
    to scrape submission pages.

    This is an async context manager - the browser is initialized once
    and reused for all requests during the context.
    """

    BASE_URL = "https://atcoder.jp"

    __cached: dict[str, List[Exercise]] = {}
    _browser: FlareSolverrCrawler | None = None

    @property
    def cached(self) -> dict[str, List[Exercise]]:
        return AtcoderJudge.__cached

    async def __aenter__(self) -> Self:
        """Initialize FlareSolverr for this context."""
        self._browser = FlareSolverrCrawler()
        await self._browser.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close browser when context ends."""
        if self._browser:
            await self._browser.__aexit__(exc_type, exc_val, exc_tb)
        return None

    @override
    def get_batch_config(self, from_exercise: str) -> dict[str, Any]:
        """AtCoder doesn't support batch config in the same way."""
        contest, problem = AtcoderExercise.parse(from_exercise)
        return {"contest": contest, "problem": problem}

    @override
    def get_exercise_url(self, code: str) -> str:
        contest, problem = AtcoderExercise.parse(code)
        return f"{self.BASE_URL}/contests/{contest}/tasks/{contest}_{problem}"

    @override
    async def crawl_exercises_batch(self, **kwargs) -> Iterable[Exercise]:
        """Fetch exercise info from AtCoder problem page.

        Note: This is a simplified implementation. In practice, you might
        want to cache exercises more aggressively since AtCoder requires
        browser automation.
        """
        contest = kwargs.get("contest")
        problem = kwargs.get("problem")
        if contest is None or problem is None:
            raise ExerciseNotFoundError

        cache_key = f"{contest}_{problem}"
        result = self.cached.get(cache_key)
        if result is not None:
            return result

        try:
            # Use browser to fetch problem page
            if self._browser is None:
                raise RuntimeError("Browser not initialized. Use async context manager.")
            exercise_url = self.get_exercise_url(cache_key)
            html_content = await self._browser.get_page_content(exercise_url, wait_for="h2")

            # Parse title from HTML - try multiple selectors
            soup = BeautifulSoup(html_content, "html.parser")
            title = ""

            # Try h2 with class first
            title_elem = soup.find("h2", class_="task-title")
            if title_elem:
                title = title_elem.get_text(strip=True)
            else:
                # Try span with class h2 inside header
                title_elem = soup.select_one("header span.h2")
                if title_elem:
                    title = title_elem.get_text(strip=True)
                else:
                    # Try any h2
                    title_elem = soup.find("h2")
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    else:
                        # Try title tag
                        title_elem = soup.find("title")
                        if title_elem:
                            # AtCoder title format: "A - Problem Name - AtCoder"
                            parts = title_elem.get_text(strip=True).split(" - ")
                            if len(parts) >= 2:
                                title = parts[1]

            exercise = AtcoderExercise(code=cache_key, title=title)
            self.cached[cache_key] = [exercise]
            return [exercise]

        except Exception:
            raise AtcoderProblemNotFoundError

    @override
    def get_submission_url(self, submission_id: str, **kwargs) -> str:
        """Get submission URL. Requires contest from kwargs or code."""
        contest = kwargs.get("contest")
        if contest is None:
            code = kwargs.get("code", "")
            if code:
                contest, _ = AtcoderExercise.parse(code)
            else:
                # Can't construct URL without contest
                return ""
        return f"{self.BASE_URL}/contests/{contest}/submissions/{submission_id}"

    @override
    async def crawl_user_submissions(
        self, user_judge: UserJudge, from_timestamp: datetime
    ) -> list[Submission]:
        """Crawl submissions for an AtCoder user after the given timestamp.

        Uses browser automation to scrape the submissions page.
        URL: https://atcoder.jp/contests/{contest}/submissions?f.User={user}
        """
        submissions = []

        try:
            if self._browser is None:
                raise RuntimeError("Browser not initialized. Use async context manager.")

            # AtCoder has a global submissions page for a user across contests
            # However, we need to iterate through contests the user participated in
            # For simplicity, we'll crawl the recent submissions page
            # which shows submissions across all contests
            url = f"{self.BASE_URL}/submissions?f.User={user_judge.handle}"

            html_content = await self._browser.get_page_content(url, wait_for="table")

            soup = BeautifulSoup(html_content, "html.parser")

            # Find the submissions table
            table = soup.find("table", class_="table")
            if not table:
                return submissions

            tbody = table.find("tbody")
            if not tbody:
                return submissions

            rows = tbody.find_all("tr")

            for row in rows:
                try:
                    cells = row.find_all("td")
                    if len(cells) < 8:
                        continue

                    # Parse submission time
                    time_cell = cells[0]
                    time_text = time_cell.get_text(strip=True)
                    submitted_at = self._parse_atcoder_time(time_text)

                    if submitted_at is None or submitted_at <= from_timestamp:
                        continue

                    # Parse problem code from link
                    problem_link = cells[1].find("a")
                    if not problem_link:
                        continue

                    problem_href = problem_link.get("href", "")
                    # Extract contest and problem from URL like /contests/abc360/tasks/abc360_a
                    match = re.search(r"/contests/([^/]+)/tasks/([^/]+)", problem_href)
                    if not match:
                        continue

                    contest = match.group(1)
                    problem_full = match.group(2)
                    # Problem code is usually {contest}_{problem_letter}
                    problem_letter = problem_full.replace(f"{contest}_", "")
                    code = f"{contest}_{problem_letter}"

                    # Parse verdict
                    verdict_cell = cells[6]  # Status column
                    verdict_text = verdict_cell.get_text(strip=True)
                    verdict = ATCODER_VERDICT_MAP.get(verdict_text)
                    if verdict is None:
                        continue

                    # Parse submission ID from link
                    submission_link = cells[9].find("a") if len(cells) > 9 else None
                    submission_id = ""
                    if submission_link:
                        submission_href = submission_link.get("href", "")
                        match = re.search(r"/submissions/(\d+)", submission_href)
                        if match:
                            submission_id = match.group(1)

                    # Get problem title
                    problem_title = problem_link.get_text(strip=True)

                    # Create exercise
                    exercise = Exercise(
                        judge=JudgeEnum.ATCODER,
                        code=code,
                        title=problem_title,
                    )

                    # Create submission
                    submission = Submission(
                        exercise=exercise,
                        user_id=user_judge.user_id,
                        verdict=verdict,
                        submission_id=submission_id,
                        submitted_at=submitted_at,
                        content="",
                        points=100 if verdict == Verdict.AC else 0,
                    )
                    submissions.append(submission)

                except Exception:
                    continue

            return submissions

        except Exception:
            return submissions

    def _parse_atcoder_time(self, time_str: str) -> datetime | None:
        """Parse AtCoder submission time string.

        Format: YYYY-MM-DD HH:MM:SS+TTTT (e.g., 2024-06-02 21:00:00+0900)
        """
        try:
            # Handle timezone offset format
            # AtCoder uses +0900 format (JST)
            if "+" in time_str:
                dt_part, tz_part = time_str.rsplit("+", 1)
                dt = datetime.strptime(dt_part.strip(), "%Y-%m-%d %H:%M:%S")
                # Parse timezone offset
                tz_hours = int(tz_part[:2])
                tz_mins = int(tz_part[2:])
                from datetime import timedelta

                offset = timedelta(hours=tz_hours, minutes=tz_mins)
                dt = dt.replace(tzinfo=timezone(offset))
                return dt.astimezone(timezone.utc)
            else:
                # No timezone, assume UTC
                return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
        except ValueError:
            return None