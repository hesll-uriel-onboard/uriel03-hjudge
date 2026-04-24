import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from hjudge.oj.models.judges import AbstractCrawler, JudgeEnum
from hjudge.oj.models.judges.codeforces import CodeforcesJudge
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
        mock_response.status_code = 200
        mock_response.content = self.response_data.get("content", "{}").encode()
        return mock_response


def make_cf_submission(
    submission_id: int,
    contest_id: int,
    problem_index: str,
    verdict: str,
    timestamp: int,
    handle: str = "testuser",
    points: int | None = None,
):
    """Helper to create a Codeforces API submission object"""
    result = {
        "id": submission_id,
        "contestId": contest_id,
        "problem": {
            "contestId": contest_id,
            "index": problem_index,
            "name": f"Problem {problem_index}",
        },
        "author": {"members": [{"handle": handle}]},
        "verdict": verdict,
        "creationTimeSeconds": timestamp,
    }
    if points is not None:
        result["points"] = points
    return result


def make_user_judge(handle: str = "testuser") -> UserJudge:
    """Helper to create a UserJudge for testing"""
    return UserJudge(
        user_id=USER_ID,
        judge=JudgeEnum.CODEFORCES,
        handle=handle,
    )


@pytest.mark.asyncio
async def test_crawl_user_submissions():
    # with - mock response with submissions
    submissions_data = [
        make_cf_submission(
            submission_id=100,
            contest_id=1234,
            problem_index="A",
            verdict="OK",
            timestamp=1738000000,  # 2025-01-27
            points=100,
        ),
        make_cf_submission(
            submission_id=101,
            contest_id=1234,
            problem_index="B",
            verdict="WRONG_ANSWER",
            timestamp=1738001000,
            points=0,
        ),
        make_cf_submission(
            submission_id=102,
            contest_id=1234,
            problem_index="A",
            verdict="TIME_LIMIT_EXCEEDED",
            timestamp=1738002000,
            points=0,
        ),
    ]

    import json

    response_content = json.dumps({"status": "OK", "result": submissions_data})
    mock_crawler = MockCrawler({"content": response_content})

    judge = CodeforcesJudge(mock_crawler)
    user_judge = make_user_judge()

    # act
    from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)
    submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

    # assert
    assert len(submissions) == 3

    # Check first submission
    assert submissions[0].submission_id == "100"
    assert submissions[0].exercise.judge == JudgeEnum.CODEFORCES
    assert submissions[0].exercise.code == "1234A"
    assert submissions[0].verdict == Verdict.AC
    assert submissions[0].user_id == USER_ID
    assert submissions[0].points == 100

    # Check second submission
    assert submissions[1].submission_id == "101"
    assert submissions[1].exercise.code == "1234B"
    assert submissions[1].verdict == Verdict.WA
    assert submissions[1].points == 0

    # Check third submission
    assert submissions[2].verdict == Verdict.TLE
    assert submissions[2].points == 0


@pytest.mark.asyncio
async def test_crawl_user_submissions_with_timestamp_filter():
    # with
    submissions_data = [
        make_cf_submission(
            submission_id=100,
            contest_id=1234,
            problem_index="A",
            verdict="OK",
            timestamp=1738000000,  # 2025-01-27
            points=100,
        ),
        make_cf_submission(
            submission_id=101,
            contest_id=1234,
            problem_index="B",
            verdict="OK",
            timestamp=1739000000,  # Later submission
            points=100,
        ),
    ]

    import json

    response_content = json.dumps({"status": "OK", "result": submissions_data})
    mock_crawler = MockCrawler({"content": response_content})

    judge = CodeforcesJudge(mock_crawler)
    user_judge = make_user_judge()

    # act - only get submissions after first one
    from_timestamp = datetime.fromtimestamp(1738001000, tz=timezone.utc)
    submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

    # assert - should only get the second one
    assert len(submissions) == 1
    assert submissions[0].submission_id == "101"


@pytest.mark.asyncio
async def test_crawl_user_submissions_empty():
    # with - empty response
    import json

    response_content = json.dumps({"status": "OK", "result": []})
    mock_crawler = MockCrawler({"content": response_content})

    judge = CodeforcesJudge(mock_crawler)
    user_judge = make_user_judge()

    # act
    from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)
    submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

    # assert
    assert len(submissions) == 0


@pytest.mark.asyncio
async def test_crawl_user_submissions_verdict_mapping():
    """Test that CF verdicts map correctly to our Verdict enum"""
    test_cases = [
        ("OK", Verdict.AC),
        ("WRONG_ANSWER", Verdict.WA),
        ("TIME_LIMIT_EXCEEDED", Verdict.TLE),
        ("RUNTIME_ERROR", Verdict.RTE),
        ("MEMORY_LIMIT_EXCEEDED", Verdict.RTE),  # Maps to RTE
        ("COMPILATION_ERROR", Verdict.CE),  # Maps to CE (updated)
    ]

    for cf_verdict, expected_verdict in test_cases:
        submission_data = [
            make_cf_submission(
                submission_id=100,
                contest_id=1234,
                problem_index="A",
                verdict=cf_verdict,
                timestamp=1738000000,
            )
        ]

        import json

        response_content = json.dumps({"status": "OK", "result": submission_data})
        mock_crawler = MockCrawler({"content": response_content})

        judge = CodeforcesJudge(mock_crawler)
        user_judge = make_user_judge()
        submissions = await judge.crawl_user_submissions(user_judge, datetime.fromtimestamp(0, tz=timezone.utc))

        assert len(submissions) == 1
        assert submissions[0].verdict == expected_verdict, f"CF verdict {cf_verdict} should map to {expected_verdict}"


def test_get_submission_url():
    judge = CodeforcesJudge(MagicMock())

    url = judge.get_submission_url("123456789", code="1234A")

    assert "codeforces.com" in url
    assert "contest/1234" in url
    assert "123456789" in url


def test_get_submission_url_gym():
    judge = CodeforcesJudge(MagicMock())

    url = judge.get_submission_url("123456789", code="100001A")

    assert "codeforces.com" in url
    assert "gym/100001" in url
    assert "123456789" in url


def test_get_exercise_url_regular():
    judge = CodeforcesJudge(MagicMock())

    url = judge.get_exercise_url("1234A")

    assert "problemset/problem/1234/A" in url


def test_get_exercise_url_gym():
    judge = CodeforcesJudge(MagicMock())

    url = judge.get_exercise_url("100001A")

    assert "gym/100001/problem/A" in url


def test_get_batch_config_regular():
    judge = CodeforcesJudge(MagicMock())

    config = judge.get_batch_config("1234A")

    assert "contest/1234" in config["url"]


def test_get_batch_config_gym():
    judge = CodeforcesJudge(MagicMock())

    config = judge.get_batch_config("100001A")

    assert "gym/100001" in config["url"]


@pytest.mark.asyncio
async def test_crawl_user_submissions_extracts_points():
    """Test that points are extracted from Codeforces API response"""
    import json

    submissions_data = [
        make_cf_submission(
            submission_id=100,
            contest_id=1234,
            problem_index="A",
            verdict="OK",
            timestamp=1738000000,
            points=100,
        ),
        make_cf_submission(
            submission_id=101,
            contest_id=1234,
            problem_index="B",
            verdict="WRONG_ANSWER",
            timestamp=1738001000,
            points=50,
        ),
    ]

    response_content = json.dumps({"status": "OK", "result": submissions_data})
    mock_crawler = MockCrawler({"content": response_content})

    judge = CodeforcesJudge(mock_crawler)
    user_judge = make_user_judge()

    # act
    from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)
    submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

    # assert
    assert len(submissions) == 2
    assert submissions[0].points == 100
    assert submissions[1].points == 50


@pytest.mark.asyncio
async def test_crawl_user_submissions_default_points_for_ac():
    """Test that AC submissions without points default to 100"""
    import json

    # AC submission without points field - should default to 100
    submissions_data = [
        make_cf_submission(
            submission_id=100,
            contest_id=1234,
            problem_index="A",
            verdict="OK",
            timestamp=1738000000,
            # No points field
        ),
    ]

    response_content = json.dumps({"status": "OK", "result": submissions_data})
    mock_crawler = MockCrawler({"content": response_content})

    judge = CodeforcesJudge(mock_crawler)
    user_judge = make_user_judge()

    # act
    from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)
    submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

    # assert - AC without points should default to 100
    assert len(submissions) == 1
    assert submissions[0].verdict == Verdict.AC
    assert submissions[0].points == 100


@pytest.mark.asyncio
async def test_crawl_user_submissions_zero_points_for_non_ac():
    """Test that non-AC submissions without points default to 0"""
    import json

    # WA submission without points field - should default to 0
    submissions_data = [
        make_cf_submission(
            submission_id=100,
            contest_id=1234,
            problem_index="A",
            verdict="WRONG_ANSWER",
            timestamp=1738000000,
            # No points field
        ),
    ]

    response_content = json.dumps({"status": "OK", "result": submissions_data})
    mock_crawler = MockCrawler({"content": response_content})

    judge = CodeforcesJudge(mock_crawler)
    user_judge = make_user_judge()

    # act
    from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)
    submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

    # assert - non-AC without points should default to 0
    assert len(submissions) == 1
    assert submissions[0].verdict == Verdict.WA
    assert submissions[0].points == 0