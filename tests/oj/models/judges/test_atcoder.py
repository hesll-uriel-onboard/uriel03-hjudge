import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.judges.atcoder import (
    AtcoderJudge,
    AtcoderExercise,
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
        judge = AtcoderJudge(MagicMock())
        url = judge.get_exercise_url("abc360_a")
        assert url == "https://atcoder.jp/contests/abc360/tasks/abc360_a"

    def test_get_submission_url(self):
        judge = AtcoderJudge(MagicMock())
        url = judge.get_submission_url("12345678", contest="abc360")
        assert url == "https://atcoder.jp/contests/abc360/submissions/12345678"

    def test_get_submission_url_with_code(self):
        judge = AtcoderJudge(MagicMock())
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

    def test_parse_atcoder_time(self):
        """Test parsing AtCoder timestamp format"""
        judge = AtcoderJudge(MagicMock())

        # Test with timezone
        dt = judge._parse_atcoder_time("2024-06-02 21:00:00+0900")
        assert dt is not None
        assert dt.month == 6
        assert dt.day == 2
        # JST is UTC+9, so 21:00 JST = 12:00 UTC
        assert dt.hour == 12

        # Test without timezone
        dt = judge._parse_atcoder_time("2024-06-02 12:00:00")
        assert dt is not None
        assert dt.hour == 12

    def test_crawl_user_submissions_mocked(self):
        """Test crawling submissions with mocked HTML response"""
        # Sample HTML table for submissions
        html_content = """
        <html>
        <body>
        <table class="table">
            <tbody>
                <tr>
                    <td>2024-06-02 21:00:00+0900</td>
                    <td><a href="/contests/abc360/tasks/abc360_a">A - Problem A</a></td>
                    <td>Python</td>
                    <td>100</td>
                    <td>100</td>
                    <td>100</td>
                    <td>AC</td>
                    <td>100</td>
                    <td>100</td>
                    <td><a href="/contests/abc360/submissions/12345678">Detail</a></td>
                </tr>
                <tr>
                    <td>2024-06-02 22:00:00+0900</td>
                    <td><a href="/contests/abc360/tasks/abc360_b">B - Problem B</a></td>
                    <td>Python</td>
                    <td>100</td>
                    <td>100</td>
                    <td>100</td>
                    <td>WA</td>
                    <td>0</td>
                    <td>0</td>
                    <td><a href="/contests/abc360/submissions/12345679">Detail</a></td>
                </tr>
            </tbody>
        </table>
        </body>
        </html>
        """

        mock_crawler = MagicMock()
        mock_crawler.get_page_content = MagicMock(return_value=html_content)

        judge = AtcoderJudge(MagicMock())
        judge._get_browser = MagicMock(return_value=mock_crawler)

        user_judge = make_user_judge()
        from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)

        submissions = judge.crawl_user_submissions(user_judge, from_timestamp)

        assert len(submissions) == 2
        assert submissions[0].submission_id == "12345678"
        assert submissions[0].exercise.code == "abc360_a"
        assert submissions[0].verdict == Verdict.AC
        assert submissions[0].points == 100

        assert submissions[1].submission_id == "12345679"
        assert submissions[1].exercise.code == "abc360_b"
        assert submissions[1].verdict == Verdict.WA
        assert submissions[1].points == 0