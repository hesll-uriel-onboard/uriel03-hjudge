import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

import pytest

from hjudge.oj.models.judges import AbstractCrawler, JudgeEnum
from hjudge.oj.models.judges.dmoj import DmojJudge, DmojExercise, DMOJ_VERDICT_MAP
from hjudge.oj.models.submission import Verdict
from hjudge.oj.models.user_judge import UserJudge

# Test user ID
USER_ID = uuid.uuid4()


class MockCrawler(AbstractCrawler):
    """Mock crawler for testing"""

    def __init__(self, response_data: dict):
        self.response_data = response_data

    def get(self, url: str, *args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = self.response_data.get("status_code", 200)
        mock_response.content = self.response_data.get("content", "{}").encode()
        return mock_response


def make_dmoj_submission(
    submission_id: int,
    problem_code: str,
    verdict: str,
    timestamp: str,
    page_index: int | None = None,
):
    """Helper to create a DMOJ API submission object"""
    result = {
        "id": submission_id,
        "problem": problem_code,
        "result": verdict,
        "date": timestamp,
    }
    if page_index is not None:
        result["page_index"] = page_index
    return result


def make_user_judge(handle: str = "testuser") -> UserJudge:
    """Helper to create a UserJudge for testing"""
    return UserJudge(
        user_id=USER_ID,
        judge=JudgeEnum.DMOJ,
        handle=handle,
    )


class TestDmojExercise:
    """Tests for DmojExercise class"""

    def test_create_from(self):
        data = {
            "code": "aplusb",
            "name": "A Plus B",
        }
        exercise = DmojExercise.create_from(data)
        assert exercise.code == "aplusb"
        assert exercise.title == "A Plus B"
        assert exercise.judge == JudgeEnum.DMOJ

    def test_create_from_empty_title(self):
        data = {
            "code": "testprob",
        }
        exercise = DmojExercise.create_from(data)
        assert exercise.code == "testprob"
        assert exercise.title == ""


class TestDmojJudge:
    """Tests for DmojJudge class"""

    def test_get_exercise_url(self):
        judge = DmojJudge(MockCrawler({}))
        url = judge.get_exercise_url("aplusb")
        assert url == "https://dmoj.ca/problem/aplusb"

    def test_get_submission_url(self):
        judge = DmojJudge(MockCrawler({}))
        url = judge.get_submission_url("123456")
        assert url == "https://dmoj.ca/submission/123456"

    @pytest.mark.asyncio
    async def test_crawl_exercises_batch(self):
        problem_data = {
            "code": "aplusb",
            "name": "A Plus B",
        }
        response = {
            "data": {
                "object": problem_data
            }
        }
        mock_crawler = MockCrawler({"content": json.dumps(response)})
        judge = DmojJudge(mock_crawler)

        exercises = list(await judge.crawl_exercises_batch("", code="aplusb"))

        assert len(exercises) == 1
        assert exercises[0].code == "aplusb"
        assert exercises[0].title == "A Plus B"
        assert exercises[0].judge == JudgeEnum.DMOJ

    @pytest.mark.asyncio
    async def test_crawl_user_submissions(self):
        submissions_data = [
            make_dmoj_submission(
                submission_id=100,
                problem_code="aplusb",
                verdict="AC",
                timestamp="2025-01-27T10:00:00+00:00",
            ),
            make_dmoj_submission(
                submission_id=101,
                problem_code="aplusb",
                verdict="WA",
                timestamp="2025-01-27T11:00:00+00:00",
            ),
            make_dmoj_submission(
                submission_id=102,
                problem_code="testprob",
                verdict="TLE",
                timestamp="2025-01-27T12:00:00+00:00",
            ),
        ]

        response = {
            "data": {
                "objects": submissions_data,
                "has_more": False
            }
        }
        mock_crawler = MockCrawler({"content": json.dumps(response)})
        judge = DmojJudge(mock_crawler)
        user_judge = make_user_judge()

        from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)
        submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

        assert len(submissions) == 3
        assert submissions[0].submission_id == "100"
        assert submissions[0].exercise.code == "aplusb"
        assert submissions[0].verdict == Verdict.AC
        assert submissions[0].user_id == USER_ID
        assert submissions[0].points == 100

        assert submissions[1].verdict == Verdict.WA
        assert submissions[1].points == 0

        assert submissions[2].exercise.code == "testprob"
        assert submissions[2].verdict == Verdict.TLE

    @pytest.mark.asyncio
    async def test_crawl_user_submissions_with_timestamp_filter(self):
        submissions_data = [
            make_dmoj_submission(
                submission_id=100,
                problem_code="aplusb",
                verdict="AC",
                timestamp="2025-01-27T10:00:00+00:00",
            ),
            make_dmoj_submission(
                submission_id=101,
                problem_code="testprob",
                verdict="AC",
                timestamp="2025-01-28T10:00:00+00:00",
            ),
        ]

        response = {
            "data": {
                "objects": submissions_data,
                "has_more": False
            }
        }
        mock_crawler = MockCrawler({"content": json.dumps(response)})
        judge = DmojJudge(mock_crawler)
        user_judge = make_user_judge()

        # Filter to only get submissions after 2025-01-27T12:00:00
        from_timestamp = datetime(2025, 1, 27, 12, 0, 0, tzinfo=timezone.utc)
        submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

        assert len(submissions) == 1
        assert submissions[0].submission_id == "101"

    @pytest.mark.asyncio
    async def test_crawl_user_submissions_empty(self):
        response = {
            "data": {
                "objects": [],
                "has_more": False
            }
        }
        mock_crawler = MockCrawler({"content": json.dumps(response)})
        judge = DmojJudge(mock_crawler)
        user_judge = make_user_judge()

        from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)
        submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

        assert len(submissions) == 0

    def test_verdict_mapping(self):
        """Test that DMOJ verdicts map correctly to our Verdict enum"""
        test_cases = [
            ("AC", Verdict.AC),
            ("WA", Verdict.WA),
            ("TLE", Verdict.TLE),
            ("MLE", Verdict.RTE),
            ("RTE", Verdict.RTE),
            ("IR", Verdict.RTE),
            ("OLE", Verdict.RTE),
            ("CE", Verdict.CE),
            ("IE", Verdict.IE),
        ]

        for dmoj_verdict, expected_verdict in test_cases:
            assert DMOJ_VERDICT_MAP.get(dmoj_verdict) == expected_verdict

    @pytest.mark.asyncio
    async def test_crawl_user_submissions_verdict_filtering(self):
        """Test that unknown verdicts are skipped"""
        submissions_data = [
            make_dmoj_submission(
                submission_id=100,
                problem_code="aplusb",
                verdict="AC",
                timestamp="2025-01-27T10:00:00+00:00",
            ),
            make_dmoj_submission(
                submission_id=101,
                problem_code="aplusb",
                verdict="UNKNOWN",
                timestamp="2025-01-27T11:00:00+00:00",
            ),
        ]

        response = {
            "data": {
                "objects": submissions_data,
                "has_more": False
            }
        }
        mock_crawler = MockCrawler({"content": json.dumps(response)})
        judge = DmojJudge(mock_crawler)
        user_judge = make_user_judge()

        from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)
        submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

        # Only the AC submission should be returned
        assert len(submissions) == 1
        assert submissions[0].submission_id == "100"