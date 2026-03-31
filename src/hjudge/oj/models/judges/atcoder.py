import re
from datetime import datetime, timezone
from typing import Any, ClassVar, Iterable, List, Self, override

import httpx

from hjudge.oj.errors import AtcoderProblemNotFoundError, ExerciseNotFoundError
from hjudge.oj.models.judges import (
    AbstractJudge,
    AbstractCrawler,
    Exercise,
    JudgeEnum,
    UserJudge,
)
from hjudge.oj.models.submission import Submission, Verdict

# Kenkoooo API base URL for AtCoder
KENKOOOO_API_URL = "https://kenkoooo.com/atcoder/atcoder-api/v3"
KENKOOOO_RESOURCES_URL = "https://kenkoooo.com/atcoder/resources"

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


class KenkooooCrawler(AbstractCrawler):
    """Crawler for AtCoder using Kenkoooo's unofficial API.

    The Kenkoooo API provides access to AtCoder submissions and problems
    without requiring authentication or browser automation.
    """

    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> Self:
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()
        return None

    def get(self, url: str, *args, **kwargs):
        """Synchronous get method for AbstractCrawler interface compatibility.

        Note: This is not used by KenkooooCrawler which operates asynchronously.
        """
        if self._client:
            return self._client.get(url, *args, **kwargs)
        return httpx.get(url, timeout=self.timeout, *args, **kwargs)

    async def get_user_submissions(
        self, user: str, from_second: int = 0
    ) -> list[dict]:
        """Get submissions for a user from Kenkoooo API.

        Args:
            user: AtCoder username
            from_second: Unix timestamp to filter submissions (only submissions after this time)

        Returns:
            List of submission objects from the API
        """
        if self._client is None:
            raise RuntimeError("Client not initialized. Use async context manager.")

        url = f"{KENKOOOO_API_URL}/user/submissions"
        response = await self._client.get(url, params={"user": user, "from_second": from_second})

        if response.status_code != 200:
            return []

        return response.json()

    async def get_problem_list(self) -> list[dict]:
        """Get all AtCoder problems from Kenkoooo resources.

        Returns:
            List of problem objects with id, contest_id, title, etc.
        """
        if self._client is None:
            raise RuntimeError("Client not initialized. Use async context manager.")

        url = f"{KENKOOOO_RESOURCES_URL}/problems.json"
        response = await self._client.get(url)

        if response.status_code != 200:
            return []

        return response.json()


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

        Expected data format (from Kenkoooo API):
        {
            "id": "abc360_a",
            "contest_id": "abc360",
            "title": "A - A Simple Problem"
        }
        Or:
        {
            "contest": "abc360",
            "problem": "a",
            "name": "A - A Simple Problem"
        }
        """
        # Handle Kenkoooo API format
        if "id" in data and "contest_id" in data:
            return cls(code=data["id"], title=data.get("title", ""))

        # Handle legacy format
        contest = data.get(AtcoderExercise.CONTEST)
        problem = data.get(AtcoderExercise.PROBLEM)
        name = data.get("name", "")
        if contest and problem:
            return cls(f"{contest}_{problem}", name)

        raise ExerciseNotFoundError


class AtcoderJudge(AbstractJudge):
    """AtCoder judge implementation using Kenkoooo's unofficial API.

    This approach is much simpler and faster than browser automation,
    and doesn't require handling Cloudflare protection or login.

    Note: The crawler parameter is required by the AbstractJudge Protocol
    but is not used since we use KenkooooCrawler internally.
    """

    BASE_URL = "https://atcoder.jp"

    __cached: dict[str, List[Exercise]] = {}
    __problems_cache: dict[str, str] = {}  # problem_id -> title
    _crawler: KenkooooCrawler | None = None

    def __init__(self, crawler: AbstractCrawler = None):
        """Initialize AtcoderJudge.

        Args:
            crawler: Required by Protocol but not used. We use KenkooooCrawler internally.
        """
        self.crawler = crawler

    @property
    def cached(self) -> dict[str, List[Exercise]]:
        return AtcoderJudge.__cached

    async def __aenter__(self) -> Self:
        """Initialize Kenkoooo crawler."""
        self._crawler = KenkooooCrawler()
        await self._crawler.__aenter__()

        # Load problem list into cache
        if not AtcoderJudge.__problems_cache:
            try:
                problems = await self._crawler.get_problem_list()
                for p in problems:
                    problem_id = p.get("id", "")
                    title = p.get("title", "")
                    if problem_id:
                        AtcoderJudge.__problems_cache[problem_id] = title
            except Exception:
                pass

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close crawler when context ends."""
        if self._crawler:
            await self._crawler.__aexit__(exc_type, exc_val, exc_tb)
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
        """Fetch exercise info using cached problem data or Kenkoooo API."""
        contest = kwargs.get("contest")
        problem = kwargs.get("problem")
        if contest is None or problem is None:
            raise ExerciseNotFoundError

        cache_key = f"{contest}_{problem}"
        result = self.cached.get(cache_key)
        if result is not None:
            return result

        # Try to get title from cache
        title = AtcoderJudge.__problems_cache.get(cache_key, "")

        # If not in cache, try to fetch problem list again
        if not title and self._crawler:
            try:
                problems = await self._crawler.get_problem_list()
                for p in problems:
                    problem_id = p.get("id", "")
                    problem_title = p.get("title", "")
                    if problem_id:
                        AtcoderJudge.__problems_cache[problem_id] = problem_title
                title = AtcoderJudge.__problems_cache.get(cache_key, "")
            except Exception:
                pass

        if not title:
            raise AtcoderProblemNotFoundError

        exercise = AtcoderExercise(code=cache_key, title=title)
        self.cached[cache_key] = [exercise]
        return [exercise]

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
        """Crawl submissions for an AtCoder user using Kenkoooo API.

        Args:
            user_judge: UserJudge with handle (AtCoder username)
            from_timestamp: Only fetch submissions after this timestamp

        Returns:
            List of Submission objects
        """
        submissions = []

        if self._crawler is None:
            return submissions

        try:
            # Convert timestamp to epoch seconds for API
            from_second = int(from_timestamp.timestamp())

            # Fetch submissions from Kenkoooo API
            api_submissions = await self._crawler.get_user_submissions(
                user=user_judge.handle, from_second=from_second
            )

            for sub in api_submissions:
                try:
                    # Parse submission time
                    epoch_second = sub.get("epoch_second", 0)
                    submitted_at = datetime.fromtimestamp(epoch_second, tz=timezone.utc)

                    if submitted_at <= from_timestamp:
                        continue

                    # Parse problem code
                    problem_id = sub.get("problem_id", "")
                    contest_id = sub.get("contest_id", "")
                    if not problem_id:
                        continue

                    # Get title from cache
                    title = AtcoderJudge.__problems_cache.get(problem_id, "")

                    # Parse verdict
                    result = sub.get("result", "")
                    verdict = ATCODER_VERDICT_MAP.get(result)
                    if verdict is None:
                        continue  # Skip unknown verdicts

                    # Parse submission ID
                    submission_id = str(sub.get("id", ""))

                    # Parse points - normalize to 100 scale
                    # AtCoder uses varying points (100-2000), but we normalize to 100 for consistency
                    points = 100 if verdict == Verdict.AC else 0

                    # Create exercise
                    exercise = Exercise(
                        judge=JudgeEnum.ATCODER,
                        code=problem_id,
                        title=title,
                    )

                    # Create submission
                    submission = Submission(
                        exercise=exercise,
                        user_id=user_judge.user_id,
                        verdict=verdict,
                        submission_id=submission_id,
                        submitted_at=submitted_at,
                        content="",
                        points=int(points) if points else 0,
                    )
                    submissions.append(submission)

                except Exception:
                    continue

            return submissions

        except Exception:
            return submissions