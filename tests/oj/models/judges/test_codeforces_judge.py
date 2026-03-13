import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.judges.codeforces import CodeforcesJudge
from hjudge.oj.models.submission import Verdict
from hjudge.oj.models.user_judge import UserJudge

# Test user ID
USER_ID = uuid.uuid4()


class MockCrawler:
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
):
    """Helper to create a Codeforces API submission object"""
    return {
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


def make_user_judge(handle: str = "testuser") -> UserJudge:
    """Helper to create a UserJudge for testing"""
    return UserJudge(
        user_id=USER_ID,
        judge=JudgeEnum.CODEFORCES,
        handle=handle,
    )


def test_crawl_user_submissions():
    # with - mock response with submissions
    submissions_data = [
        make_cf_submission(
            submission_id=100,
            contest_id=1234,
            problem_index="A",
            verdict="OK",
            timestamp=1738000000,  # 2025-01-27
        ),
        make_cf_submission(
            submission_id=101,
            contest_id=1234,
            problem_index="B",
            verdict="WRONG_ANSWER",
            timestamp=1738001000,
        ),
        make_cf_submission(
            submission_id=102,
            contest_id=1234,
            problem_index="A",
            verdict="TIME_LIMIT_EXCEEDED",
            timestamp=1738002000,
        ),
    ]

    import json

    response_content = json.dumps({"status": "OK", "result": submissions_data})
    mock_crawler = MockCrawler({"content": response_content})

    judge = CodeforcesJudge(mock_crawler)
    user_judge = make_user_judge()

    # act
    from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)
    submissions = judge.crawl_user_submissions(user_judge, from_timestamp)

    # assert
    assert len(submissions) == 3

    # Check first submission
    assert submissions[0].submission_id == "100"
    assert submissions[0].exercise.judge == JudgeEnum.CODEFORCES
    assert submissions[0].exercise.code == "1234A"
    assert submissions[0].verdict == Verdict.AC
    assert submissions[0].user_id == USER_ID

    # Check second submission
    assert submissions[1].submission_id == "101"
    assert submissions[1].exercise.code == "1234B"
    assert submissions[1].verdict == Verdict.WA

    # Check third submission
    assert submissions[2].verdict == Verdict.TLE


def test_crawl_user_submissions_with_timestamp_filter():
    # with
    submissions_data = [
        make_cf_submission(
            submission_id=100,
            contest_id=1234,
            problem_index="A",
            verdict="OK",
            timestamp=1738000000,  # 2025-01-27
        ),
        make_cf_submission(
            submission_id=101,
            contest_id=1234,
            problem_index="B",
            verdict="OK",
            timestamp=1739000000,  # Later submission
        ),
    ]

    import json

    response_content = json.dumps({"status": "OK", "result": submissions_data})
    mock_crawler = MockCrawler({"content": response_content})

    judge = CodeforcesJudge(mock_crawler)
    user_judge = make_user_judge()

    # act - only get submissions after first one
    from_timestamp = datetime.fromtimestamp(1738001000, tz=timezone.utc)
    submissions = judge.crawl_user_submissions(user_judge, from_timestamp)

    # assert - should only get the second one
    assert len(submissions) == 1
    assert submissions[0].submission_id == "101"


def test_crawl_user_submissions_empty():
    # with - empty response
    import json

    response_content = json.dumps({"status": "OK", "result": []})
    mock_crawler = MockCrawler({"content": response_content})

    judge = CodeforcesJudge(mock_crawler)
    user_judge = make_user_judge()

    # act
    from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)
    submissions = judge.crawl_user_submissions(user_judge, from_timestamp)

    # assert
    assert len(submissions) == 0


def test_crawl_user_submissions_verdict_mapping():
    """Test that CF verdicts map correctly to our Verdict enum"""
    test_cases = [
        ("OK", Verdict.AC),
        ("WRONG_ANSWER", Verdict.WA),
        ("TIME_LIMIT_EXCEEDED", Verdict.TLE),
        ("RUNTIME_ERROR", Verdict.RTE),
        ("MEMORY_LIMIT_EXCEEDED", Verdict.RTE),  # Maps to RTE
        ("COMPILATION_ERROR", Verdict.RTE),  # Maps to RTE
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
        submissions = judge.crawl_user_submissions(user_judge, datetime.fromtimestamp(0, tz=timezone.utc))

        assert len(submissions) == 1
        assert submissions[0].verdict == expected_verdict, f"CF verdict {cf_verdict} should map to {expected_verdict}"


def test_get_submission_url():
    judge = CodeforcesJudge(MagicMock())

    url = judge.get_submission_url("123456789", code="1234A")

    assert "codeforces.com" in url
    assert "1234" in url
    assert "123456789" in url