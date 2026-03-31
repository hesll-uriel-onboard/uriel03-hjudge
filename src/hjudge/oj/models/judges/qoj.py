import re
from datetime import datetime, timezone
from typing import Any, Iterable, List, Self, override

from bs4 import BeautifulSoup

from hjudge.oj.errors import ExerciseNotFoundError, QojProblemNotFoundError
from hjudge.oj.models.judges import (
    AbstractJudge,
    Exercise,
    JudgeEnum,
    UserJudge,
)
from hjudge.oj.models.submission import Submission, Verdict
from hjudge.oj.services.browser import AsyncBrowserCrawler

# Mapping from QOJ verdicts to our Verdict enum
QOJ_VERDICT_MAP = {
    "Accepted": Verdict.AC,
    "Wrong Answer": Verdict.WA,
    "Time Limit Exceeded": Verdict.TLE,
    "Runtime Error": Verdict.RTE,
    "Memory Limit Exceeded": Verdict.RTE,
    "Output Limit Exceeded": Verdict.RTE,
    "Compile Error": Verdict.CE,
    "Internal Error": Verdict.IE,
    # Short forms
    "AC": Verdict.AC,
    "WA": Verdict.WA,
    "TLE": Verdict.TLE,
    "RE": Verdict.RTE,
    "MLE": Verdict.RTE,
    "OLE": Verdict.RTE,
    "CE": Verdict.CE,
    "IE": Verdict.IE,
}


class QojExercise(Exercise):
    """QOJ exercise with numeric problem codes."""

    def __init__(self, code: str, title: str = ""):
        super().__init__(judge=JudgeEnum.QOJ, code=code, title=title)

    @override
    @classmethod
    def create_from(cls, data: dict, *args, **kwargs) -> Self:
        """Create QojExercise from parsed data.

        Expected data format:
        {
            "code": "1",
            "name": "A + B Problem"
        }
        """
        code = str(data.get("code", ""))
        name = data.get("name", "")
        return cls(code=code, title=name)


class QojJudge(AbstractJudge):
    """QOJ judge implementation using browser automation.

    QOJ requires login to view submissions. We use Playwright with
    playwright-stealth to bypass Cloudflare and login.

    This is an async context manager - the browser is initialized once
    and reused for all requests during the context.
    """

    BASE_URL = "https://qoj.ac"

    __cached: dict[str, List[Exercise]] = {}
    _browser: AsyncBrowserCrawler | None = None

    @property
    def cached(self) -> dict[str, List[Exercise]]:
        return QojJudge.__cached

    async def __aenter__(self) -> Self:
        """Initialize AsyncBrowserCrawler for Cloudflare bypass and login."""
        self._browser = AsyncBrowserCrawler(headless=True, bypass_cloudflare=True)
        await self._browser.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close browser when context ends."""
        if self._browser:
            await self._browser.__aexit__(exc_type, exc_val, exc_tb)
        return None

    @override
    def get_batch_config(self, from_exercise: str) -> dict[str, Any]:
        """QOJ doesn't support batch config in the same way."""
        return {"code": from_exercise}

    @override
    def get_exercise_url(self, code: str) -> str:
        return f"{self.BASE_URL}/problem/{code}"

    @override
    async def crawl_exercises_batch(self, **kwargs) -> Iterable[Exercise]:
        """Fetch exercise info from QOJ problem page."""
        code = kwargs.get("code")
        if code is None:
            raise ExerciseNotFoundError

        result = self.cached.get(code)
        if result is not None:
            return result

        try:
            if self._browser is None:
                raise RuntimeError(
                    "Browser not initialized. Use async context manager."
                )
            exercise_url = self.get_exercise_url(code)
            html_content = await self._browser.get_page_content(
                exercise_url, wait_for="h1"
            )

            # Parse title from HTML - try multiple selectors
            soup = BeautifulSoup(html_content, "html.parser")
            title = ""

            # Try h1 with class page-header first
            title_elem = soup.find("h1", class_="page-header")
            if title_elem:
                title = title_elem.get_text(strip=True)
            else:
                # Try any h1 with text-center
                title_elem = soup.select_one("h1.page-header.text-center")
                if title_elem:
                    title = title_elem.get_text(strip=True)
                else:
                    # Try any h1
                    title_elem = soup.find("h1")
                    if title_elem:
                        text = title_elem.get_text(strip=True)
                        # Skip if it's just the site name
                        if text and text not in ["QOJ.ac", "QOJ"]:
                            title = text
                        else:
                            # Fallback to title tag
                            title_elem = soup.find("title")
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                for suffix in [" - QOJ", " | QOJ", " - QOJ.ac", " | QOJ.ac"]:
                                    if title.endswith(suffix):
                                        title = title[:-len(suffix)]
                                        break

            exercise = QojExercise(code=code, title=title)
            self.cached[code] = [exercise]
            return [exercise]

        except Exception:
            raise QojProblemNotFoundError

    @override
    def get_submission_url(self, submission_id: str, **kwargs) -> str:
        return f"{self.BASE_URL}/submission/{submission_id}"

    @override
    async def crawl_user_submissions(
        self, user_judge: UserJudge, from_timestamp: datetime
    ) -> list[Submission]:
        """Crawl submissions for a QOJ user after the given timestamp.

        Uses browser automation to scrape the submissions page.
        URL: https://qoj.ac/submissions?submitter={handle}&page={page}
        """
        submissions = []
        page = 1

        try:
            if self._browser is None:
                raise RuntimeError(
                    "Browser not initialized. Use async context manager."
                )

            # QOJ paginates submissions
            while True:
                url = f"{self.BASE_URL}/submissions?submitter={user_judge.handle}&page={page}"
                html_content = await self._browser.get_page_content(
                    url, wait_for="table"
                )

                soup = BeautifulSoup(html_content, "html.parser")

                # Find the submissions table
                table = soup.find("table")
                if not table:
                    break

                tbody = table.find("tbody")
                if not tbody:
                    break

                rows = tbody.find_all("tr")
                if not rows:
                    break

                found_old_submission = False

                for row in rows:
                    try:
                        cells = row.find_all("td")
                        if len(cells) < 6:
                            continue

                        # Parse submission ID from first cell link
                        first_link = cells[0].find("a")
                        if not first_link:
                            continue
                        submission_href = first_link.get("href", "")
                        match = re.search(r"/submission/(\d+)", submission_href)
                        if not match:
                            continue
                        submission_id = match.group(1)

                        # Parse submission time
                        time_cell = cells[1]
                        time_text = time_cell.get_text(strip=True)
                        submitted_at = self._parse_qoj_time(time_text)

                        if submitted_at is None:
                            continue
                        if submitted_at <= from_timestamp:
                            found_old_submission = True
                            continue

                        # Parse problem code
                        problem_cell = cells[2]
                        problem_link = problem_cell.find("a")
                        if not problem_link:
                            continue
                        problem_href = problem_link.get("href", "")
                        match = re.search(r"/problem/([^/]+)", problem_href)
                        if not match:
                            continue
                        problem_code = match.group(1)
                        problem_title = problem_link.get_text(strip=True)

                        # Parse verdict
                        verdict_cell = cells[3]
                        verdict_text = verdict_cell.get_text(strip=True)
                        verdict = QOJ_VERDICT_MAP.get(verdict_text)
                        if verdict is None:
                            # Try partial match
                            for key, val in QOJ_VERDICT_MAP.items():
                                if key in verdict_text:
                                    verdict = val
                                    break
                        if verdict is None:
                            continue

                        # Create exercise
                        exercise = Exercise(
                            judge=JudgeEnum.QOJ,
                            code=problem_code,
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

                # Stop if we found old submissions or there are no more pages
                if found_old_submission or len(rows) < 20:
                    break

                page += 1

            return submissions

        except Exception:
            return submissions

    def _parse_qoj_time(self, time_str: str) -> datetime | None:
        """Parse QOJ submission time string.

        QOJ uses various formats like:
        - 2024-06-02 21:00:00
        - 2024-06-02T21:00:00Z
        - Relative times like "2 hours ago" (not handled)
        """
        try:
            # Try ISO format with Z
            if "T" in time_str and "Z" in time_str:
                return datetime.fromisoformat(time_str.replace("Z", "+00:00"))

            # Try simple format
            dt = datetime.strptime(time_str.strip(), "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
