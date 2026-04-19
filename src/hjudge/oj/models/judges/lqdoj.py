from datetime import datetime, timezone
from typing import Any, Iterable, List, Self, override

from bs4 import BeautifulSoup

from hjudge.oj.errors import ExerciseNotFoundError, LqdojProblemNotFoundError
from hjudge.oj.models.judges import (
    AbstractJudge,
    Exercise,
    JudgeEnum,
    UserJudge,
)
from hjudge.oj.models.submission import Submission, Verdict
from hjudge.oj.services.browser import FlareSolverrCrawler

# Mapping from LQDOJ verdicts to our Verdict enum
# LQDOJ uses DMOJ platform, so verdicts are similar
LQDOJ_VERDICT_MAP = {
    "AC": Verdict.AC,
    "WA": Verdict.WA,
    "TLE": Verdict.TLE,
    "MLE": Verdict.RTE,
    "RTE": Verdict.RTE,
    "IR": Verdict.RTE,  # Invalid Return
    "OLE": Verdict.RTE,  # Output Limit Exceeded
    "CE": Verdict.CE,
    "IE": Verdict.IE,  # Internal Error
    "SC": Verdict.WA,  # Short Answer / Skipped
}


class LqdojExercise(Exercise):
    """LQDOJ exercise with simple code-to-title mapping"""

    def __init__(self, code: str, title: str = ""):
        super().__init__(judge=JudgeEnum.LQDOJ, code=code, title=title)

    @override
    @classmethod
    def create_from(cls, data: dict, *args, **kwargs) -> Self:
        """Create LqdojExercise from parsed data.

        Expected data format:
        {
            "code": "aplusb",
            "name": "A Plus B"
        }
        """
        code = data.get("code", "")
        name = data.get("name", "")
        return cls(code=code, title=name)


class LqdojJudge(AbstractJudge):
    """LQDOJ judge implementation using browser automation.

    LQDOJ's API has been removed, so we use Playwright to scrape the site.
    Cloudflare protection requires FlareSolverr for bypass.

    This is an async context manager - the browser is initialized once
    and reused for all requests during the context.
    """

    BASE_URL = "https://lqdoj.edu.vn"

    __cached: dict[str, List[Exercise]] = {}
    _browser: FlareSolverrCrawler | None = None

    @property
    def cached(self) -> dict[str, List[Exercise]]:
        return LqdojJudge.__cached

    async def __aenter__(self) -> Self:
        """Initialize FlareSolverr for Cloudflare bypass."""
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
        """LQDOJ doesn't need batch config - problems are fetched individually."""
        return {"code": from_exercise}

    @override
    def get_exercise_url(self, code: str) -> str:
        return f"{self.BASE_URL}/problem/{code}"

    @override
    async def crawl_exercises_batch(self, **kwargs) -> Iterable[Exercise]:
        """Fetch a single problem from LQDOJ using browser automation."""
        code = kwargs.get("code")
        if code is None:
            raise ExerciseNotFoundError

        result = self.cached.get(code)
        if result is not None:
            return result

        try:
            if self._browser is None:
                raise RuntimeError("Browser not initialized. Use async context manager.")
            exercise_url = self.get_exercise_url(code)
            html_content = await self._browser.get_page_content(
                exercise_url, wait_for="h2.title-row"
            )

            soup = BeautifulSoup(html_content, "html.parser")
            title = ""

            # Try h2 with class title-row first
            title_elem = soup.find("h2", class_="title-row")
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
                        title = title_elem.get_text(strip=True)
                        # Remove common suffixes
                        for suffix in [" - LQDOJ", " | LQDOJ"]:
                            if title.endswith(suffix):
                                title = title[:-len(suffix)]
                                break

            exercise = LqdojExercise(code=code, title=title)
            self.cached[code] = [exercise]
            return [exercise]

        except Exception:
            raise LqdojProblemNotFoundError

    @override
    def get_submission_url(self, submission_id: str, **kwargs) -> str:
        return f"{self.BASE_URL}/submission/{submission_id}"

    @override
    async def crawl_user_submissions(
        self, user_judge: UserJudge, from_timestamp: datetime
    ) -> list[Submission]:
        """Crawl submissions for a LQDOJ user after the given timestamp.

        Uses browser automation to scrape the submissions page.
        URL: https://lqdoj.edu.vn/submissions/user/{handle}/?page={page}
        """
        submissions = []
        page = 1

        try:
            if self._browser is None:
                raise RuntimeError("Browser not initialized. Use async context manager.")

            while True:
                url = f"{self.BASE_URL}/submissions/user/{user_judge.handle}/?page={page}"
                html_content = await self._browser.get_page_content(
                    url, wait_for="#submissions-table"
                )

                soup = BeautifulSoup(html_content, "html.parser")
                submissions_div = soup.find("div", id="submissions-table")

                if not submissions_div:
                    break

                rows = submissions_div.find_all("div", class_="submission-row")
                if not rows:
                    break

                found_old_submission = False

                for row in rows:
                    try:
                        # Parse submission_id from div id
                        submission_id = row.get("id", "")
                        if not submission_id:
                            continue

                        # Parse problem code from link
                        problem_div = row.find("div", class_="sub-problem")
                        if not problem_div:
                            continue
                        problem_link = problem_div.find("a")
                        if not problem_link:
                            continue

                        problem_href = problem_link.get("href", "")
                        problem_code = problem_href.replace("/problem/", "")
                        problem_title = problem_link.get_text(strip=True)

                        # Parse verdict from state div class
                        state_div = row.find("div", class_="state")
                        if not state_div:
                            continue

                        state_classes = state_div.get("class", [])
                        verdict_class = ""
                        for cls in state_classes:
                            if cls in LQDOJ_VERDICT_MAP:
                                verdict_class = cls
                                break

                        verdict = LQDOJ_VERDICT_MAP.get(verdict_class)
                        if verdict is None:
                            continue  # Skip unknown verdicts

                        # Parse timestamp from data-iso attribute
                        time_span = row.find("span", class_="time-with-rel")
                        if not time_span:
                            continue

                        timestamp_str = time_span.get("data-iso", "")
                        if not timestamp_str:
                            continue

                        try:
                            submitted_at = datetime.fromisoformat(timestamp_str)
                            if submitted_at.tzinfo is None:
                                submitted_at = submitted_at.replace(
                                    tzinfo=timezone.utc
                                )
                        except ValueError:
                            continue

                        # Skip if before from_timestamp
                        if submitted_at <= from_timestamp:
                            found_old_submission = True
                            continue

                        # Create exercise
                        exercise = Exercise(
                            judge=JudgeEnum.LQDOJ,
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
                # LQDOJ shows 50 submissions per page
                if found_old_submission or len(rows) < 50:
                    break

                # Check if there's a next page
                pagination = soup.find("ul", class_="pagination")
                if not pagination:
                    break

                # Check if there's a link to the next page
                next_link = pagination.find("a", href=True)
                if not next_link:
                    break

                page += 1

            return submissions

        except Exception:
            return submissions
