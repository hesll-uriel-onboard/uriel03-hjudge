from datetime import datetime, timezone
from json import JSONDecoder
from typing import Any, Iterable, List, Self, override

from hjudge.commons.endpoints.status_codes import HTTP_200_OK
from hjudge.oj.errors import DmojProblemNotFoundError, ExerciseNotFoundError
from hjudge.oj.models.judges import (
    AbstractJudge,
    Exercise,
    JudgeEnum,
    UserJudge,
)
from hjudge.oj.models.submission import Submission, Verdict

# Mapping from DMOJ verdicts to our Verdict enum
DMOJ_VERDICT_MAP = {
    "AC": Verdict.AC,
    "WA": Verdict.WA,
    "TLE": Verdict.TLE,
    "MLE": Verdict.RTE,
    "RTE": Verdict.RTE,
    "IR": Verdict.RTE,  # Invalid Return
    "OLE": Verdict.RTE,  # Output Limit Exceeded
    "CE": Verdict.CE,
    "IE": Verdict.IE,  # Internal Error
}


class DmojExercise(Exercise):
    """DMOJ exercise with simple code-to-title mapping"""

    def __init__(self, code: str, title: str = ""):
        super().__init__(judge=JudgeEnum.DMOJ, code=code, title=title)

    @override
    @classmethod
    def create_from(cls, data: dict, *args, **kwargs) -> Self:
        """Create DmojExercise from DMOJ API response data.

        Expected data format:
        {
            "code": "aplusb",
            "name": "A Plus B",
            ...
        }
        """
        code = data.get("code", "")
        name = data.get("name", "")
        return cls(code=code, title=name)


class DmojJudge(AbstractJudge):
    """DMOJ judge implementation using REST API"""

    BASE_URL = "https://dmoj.ca"
    API_URL = f"{BASE_URL}/api/v2"

    __cached: dict[str, List[Exercise]] = {}

    @property
    def cached(self) -> dict[str, List[Exercise]]:
        return DmojJudge.__cached

    @override
    def get_batch_config(self, from_exercise: str) -> dict[str, Any]:
        """DMOJ doesn't need batch config - problems are fetched individually"""
        return {"code": from_exercise}

    @override
    def get_exercise_url(self, code: str) -> str:
        return f"{self.BASE_URL}/problem/{code}"

    @override
    def crawl_exercises_batch(self, url: str, **kwargs) -> Iterable[Exercise]:
        """Fetch a single problem from DMOJ API.

        DMOJ doesn't have a batch endpoint for problems, so we fetch individually.
        """
        code = kwargs.get("code")
        if code is None:
            raise ExerciseNotFoundError

        result = self.cached.get(code)
        if result is not None:
            return result

        try:
            api_url = f"{self.API_URL}/problem/{code}"
            response = self.crawler.get(api_url)
            if response.status_code != HTTP_200_OK:
                raise DmojProblemNotFoundError

            data = JSONDecoder().decode(response.content.decode())
            problem_data = data.get("data", {}).get("object", {})
            if not problem_data:
                raise DmojProblemNotFoundError

            exercise = DmojExercise.create_from(data=problem_data)
            self.cached[code] = [exercise]
            return [exercise]

        except DmojProblemNotFoundError:
            raise
        except Exception:
            raise ExerciseNotFoundError

    @override
    def get_submission_url(self, submission_id: str, **kwargs) -> str:
        return f"{self.BASE_URL}/submission/{submission_id}"

    @override
    def crawl_user_submissions(
        self, user_judge: UserJudge, from_timestamp: datetime
    ) -> list[Submission]:
        """Crawl submissions for a DMOJ user after the given timestamp.

        Uses DMOJ API: GET /api/v2/submissions?user={username}
        Supports pagination with page_index parameter.
        """
        submissions = []
        page_index = None

        try:
            while True:
                # Build URL with optional pagination
                url = f"{self.API_URL}/submissions?user={user_judge.handle}"
                if page_index is not None:
                    url += f"&page_index={page_index}"

                response = self.crawler.get(url)
                if response.status_code != HTTP_200_OK:
                    break

                data = JSONDecoder().decode(response.content.decode())
                objects = data.get("data", {}).get("objects", [])

                if not objects:
                    break

                for sub_data in objects:
                    # Parse submission timestamp
                    date_str = sub_data.get("date", "")
                    if not date_str:
                        continue

                    try:
                        # Parse ISO 8601 format: 2014-03-29T00:35:48+00:00
                        submitted_at = datetime.fromisoformat(date_str)
                        if submitted_at.tzinfo is None:
                            submitted_at = submitted_at.replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue

                    # Skip if before from_timestamp
                    if submitted_at <= from_timestamp:
                        continue

                    # Get verdict
                    result = sub_data.get("result", "")
                    verdict = DMOJ_VERDICT_MAP.get(result)
                    if verdict is None:
                        continue  # Skip submissions without valid verdict

                    # Get problem info
                    problem_code = sub_data.get("problem", "")
                    if not problem_code:
                        continue

                    # Create exercise
                    exercise = Exercise(
                        judge=JudgeEnum.DMOJ,
                        code=problem_code,
                        title="",  # Title not included in submission response
                    )

                    # Create submission
                    submission = Submission(
                        exercise=exercise,
                        user_id=user_judge.user_id,
                        verdict=verdict,
                        submission_id=str(sub_data.get("id", "")),
                        submitted_at=submitted_at,
                        content="",
                        points=100 if verdict == Verdict.AC else 0,
                    )
                    submissions.append(submission)

                # Check for more pages
                has_more = data.get("data", {}).get("has_more", False)
                if not has_more:
                    break

                # Get next page index from the last object
                page_index = objects[-1].get("page_index") if objects else None
                if page_index is None:
                    break

            return submissions

        except Exception:
            return submissions