import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.judges.atcoder import (
    AtcoderJudge,
    AtcoderExercise,
    KenkooooCrawler,
    ATCODER_VERDICT_MAP,
)
from hjudge.oj.models.submission import Verdict
from hjudge.oj.models.user_judge import UserJudge

# Test user ID
USER_ID = uuid.uuid4()


def make_user_judge(handle: str = "testuser") -> UserJudge:
    """Helper to create a UserJudge for testing"""
    return UserJudge(
        user_id=USER_ID,
        judge=JudgeEnum.ATCODER,
        handle=handle,
    )


def make_kenkoooo_submission(
    submission_id: int,
    problem_id: str,
    contest_id: str,
    result: str,
    epoch_second: int,
    point: float = 100.0,  # Points from API (normalized to 100 in code)
):
    """Helper to create a Kenkoooo API submission object"""
    return {
        "id": submission_id,
        "epoch_second": epoch_second,
        "problem_id": problem_id,
        "contest_id": contest_id,
        "user_id": "testuser",
        "language": "Python",
        "point": point,
        "length": 100,
        "result": result,
        "execution_time": 10,
    }


class TestAtcoderExercise:
    """Tests for AtcoderExercise class"""

    def test_create_from(self):
        data = {
            "contest": "abc360",
            "problem": "a",
            "name": "A - A Simple Problem",
        }
        exercise = AtcoderExercise.create_from(data)
        assert exercise.code == "abc360_a"
        assert exercise.title == "A - A Simple Problem"
        assert exercise.judge == JudgeEnum.ATCODER

    def test_create_from_kenkoooo_format(self):
        """Test creating from Kenkoooo API format"""
        data = {
            "id": "abc360_a",
            "contest_id": "abc360",
            "title": "A - A Simple Problem",
        }
        exercise = AtcoderExercise.create_from(data)
        assert exercise.code == "abc360_a"
        assert exercise.title == "A - A Simple Problem"
        assert exercise.judge == JudgeEnum.ATCODER

    def test_parse(self):
        contest, problem = AtcoderExercise.parse("abc360_a")
        assert contest == "abc360"
        assert problem == "a"

    def test_parse_uppercase(self):
        contest, problem = AtcoderExercise.parse("ABC360_A")
        assert contest == "abc360"
        assert problem == "a"

    def test_init(self):
        exercise = AtcoderExercise("abc360_a", "Test Problem")
        assert exercise.code == "abc360_a"
        assert exercise.title == "Test Problem"
        assert exercise.contest == "abc360"
        assert exercise.problem == "a"


class TestAtcoderJudge:
    """Tests for AtcoderJudge class"""

    def test_get_exercise_url(self):
        judge = AtcoderJudge()
        url = judge.get_exercise_url("abc360_a")
        assert url == "https://atcoder.jp/contests/abc360/tasks/abc360_a"

    def test_get_submission_url(self):
        judge = AtcoderJudge()
        url = judge.get_submission_url("12345678", contest="abc360")
        assert url == "https://atcoder.jp/contests/abc360/submissions/12345678"

    def test_get_submission_url_with_code(self):
        judge = AtcoderJudge()
        url = judge.get_submission_url("12345678", code="abc360_a")
        assert url == "https://atcoder.jp/contests/abc360/submissions/12345678"

    def test_verdict_mapping(self):
        """Test that AtCoder verdicts map correctly to our Verdict enum"""
        test_cases = [
            ("AC", Verdict.AC),
            ("WA", Verdict.WA),
            ("TLE", Verdict.TLE),
            ("RE", Verdict.RTE),
            ("MLE", Verdict.RTE),
            ("OLE", Verdict.RTE),
            ("CE", Verdict.CE),
            ("IE", Verdict.IE),
        ]

        for atcoder_verdict, expected_verdict in test_cases:
            assert ATCODER_VERDICT_MAP.get(atcoder_verdict) == expected_verdict

    @pytest.mark.asyncio
    async def test_crawl_user_submissions_mocked(self):
        """Test crawling submissions with mocked Kenkoooo API response"""
        # Mock Kenkoooo API submissions
        api_submissions = [
            make_kenkoooo_submission(
                submission_id=12345678,
                problem_id="abc360_a",
                contest_id="abc360",
                result="AC",
                epoch_second=1717335600,  # 2024-06-02 12:00:00 UTC
                point=100.0,
            ),
            make_kenkoooo_submission(
                submission_id=12345679,
                problem_id="abc360_b",
                contest_id="abc360",
                result="WA",
                epoch_second=1717339200,  # 2024-06-02 13:00:00 UTC
                point=0.0,
            ),
        ]

        # Mock problem list for titles
        problems_list = [
            {"id": "abc360_a", "contest_id": "abc360", "title": "A - Problem A"},
            {"id": "abc360_b", "contest_id": "abc360", "title": "B - Problem B"},
        ]

        # Create mock crawler that returns API data
        mock_crawler = MagicMock()

        async def mock_get_user_submissions(user, from_second=0):
            return api_submissions

        async def mock_get_problem_list():
            return problems_list

        mock_crawler.get_user_submissions = AsyncMock(side_effect=mock_get_user_submissions)
        mock_crawler.get_problem_list = AsyncMock(side_effect=mock_get_problem_list)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)

        judge = AtcoderJudge()
        judge._crawler = mock_crawler

        # Pre-populate problems cache
        AtcoderJudge.__problems_cache = {
            "abc360_a": "A - Problem A",
            "abc360_b": "B - Problem B",
        }

        user_judge = make_user_judge()
        from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)

        submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

        assert len(submissions) == 2
        assert submissions[0].submission_id == "12345678"
        assert submissions[0].exercise.code == "abc360_a"
        assert submissions[0].verdict == Verdict.AC
        assert submissions[0].points == 100

        assert submissions[1].submission_id == "12345679"
        assert submissions[1].exercise.code == "abc360_b"
        assert submissions[1].verdict == Verdict.WA
        assert submissions[1].points == 0

        # Clear cache to not affect other tests
        AtcoderJudge.__problems_cache = {}

    @pytest.mark.asyncio
    async def test_crawl_user_submissions_with_timestamp_filter(self):
        """Test that submissions before from_timestamp are filtered"""
        api_submissions = [
            make_kenkoooo_submission(
                submission_id=12345678,
                problem_id="abc360_a",
                contest_id="abc360",
                result="AC",
                epoch_second=1717335600,  # 2024-06-02 12:00:00 UTC
            ),
            make_kenkoooo_submission(
                submission_id=12345679,
                problem_id="abc360_b",
                contest_id="abc360",
                result="AC",
                epoch_second=1717399200,  # 2024-06-02 18:00:00 UTC (later)
            ),
        ]

        mock_crawler = MagicMock()
        mock_crawler.get_user_submissions = AsyncMock(return_value=api_submissions)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)

        judge = AtcoderJudge()
        judge._crawler = mock_crawler
        AtcoderJudge.__problems_cache = {"abc360_a": "A", "abc360_b": "B"}

        user_judge = make_user_judge()
        # Filter to only get submissions after 2024-06-02 14:00:00 UTC
        from_timestamp = datetime(2024, 6, 2, 14, 0, 0, tzinfo=timezone.utc)

        submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

        assert len(submissions) == 1
        assert submissions[0].submission_id == "12345679"

        AtcoderJudge.__problems_cache = {}

    @pytest.mark.asyncio
    async def test_crawl_user_submissions_unknown_verdict(self):
        """Test that unknown verdicts are skipped"""
        api_submissions = [
            make_kenkoooo_submission(
                submission_id=12345678,
                problem_id="abc360_a",
                contest_id="abc360",
                result="AC",
                epoch_second=1717335600,
            ),
            make_kenkoooo_submission(
                submission_id=12345679,
                problem_id="abc360_b",
                contest_id="abc360",
                result="UNKNOWN",  # Unknown verdict
                epoch_second=1717339200,
            ),
        ]

        mock_crawler = MagicMock()
        mock_crawler.get_user_submissions = AsyncMock(return_value=api_submissions)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)

        judge = AtcoderJudge()
        judge._crawler = mock_crawler
        AtcoderJudge.__problems_cache = {"abc360_a": "A", "abc360_b": "B"}

        user_judge = make_user_judge()
        from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)

        submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

        # Only AC submission should be returned
        assert len(submissions) == 1
        assert submissions[0].submission_id == "12345678"

        AtcoderJudge.__problems_cache = {}