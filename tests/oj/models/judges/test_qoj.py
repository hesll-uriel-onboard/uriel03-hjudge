import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.judges.qoj import QojJudge, QojExercise, QOJ_VERDICT_MAP
from hjudge.oj.models.submission import Verdict
from hjudge.oj.models.user_judge import UserJudge

# Test user ID
USER_ID = uuid.uuid4()


def make_user_judge(handle: str = "testuser") -> UserJudge:
    """Helper to create a UserJudge for testing"""
    return UserJudge(
        user_id=USER_ID,
        judge=JudgeEnum.QOJ,
        handle=handle,
    )


class TestQojExercise:
    """Tests for QojExercise class"""

    def test_create_from(self):
        data = {
            "code": "1",
            "name": "A + B Problem",
        }
        exercise = QojExercise.create_from(data)
        assert exercise.code == "1"
        assert exercise.title == "A + B Problem"
        assert exercise.judge == JudgeEnum.QOJ

    def test_create_from_numeric_code(self):
        data = {
            "code": 123,
            "name": "Test Problem",
        }
        exercise = QojExercise.create_from(data)
        assert exercise.code == "123"
        assert exercise.title == "Test Problem"

    def test_init(self):
        exercise = QojExercise("1", "A + B Problem")
        assert exercise.code == "1"
        assert exercise.title == "A + B Problem"
        assert exercise.judge == JudgeEnum.QOJ


class TestQojJudge:
    """Tests for QojJudge class"""

    def test_get_exercise_url(self):
        judge = QojJudge(MagicMock())
        url = judge.get_exercise_url("1")
        assert url == "https://qoj.ac/problem/1"

    def test_get_submission_url(self):
        judge = QojJudge(MagicMock())
        url = judge.get_submission_url("123456")
        assert url == "https://qoj.ac/submission/123456"

    def test_verdict_mapping(self):
        """Test that QOJ verdicts map correctly to our Verdict enum"""
        test_cases = [
            ("Accepted", Verdict.AC),
            ("Wrong Answer", Verdict.WA),
            ("Time Limit Exceeded", Verdict.TLE),
            ("Runtime Error", Verdict.RTE),
            ("Memory Limit Exceeded", Verdict.RTE),
            ("Compile Error", Verdict.CE),
            ("Internal Error", Verdict.IE),
            # Short forms
            ("AC", Verdict.AC),
            ("WA", Verdict.WA),
            ("TLE", Verdict.TLE),
            ("RE", Verdict.RTE),
            ("CE", Verdict.CE),
            ("IE", Verdict.IE),
        ]

        for qoj_verdict, expected_verdict in test_cases:
            assert QOJ_VERDICT_MAP.get(qoj_verdict) == expected_verdict

    def test_parse_qoj_time(self):
        """Test parsing QOJ timestamp format"""
        judge = QojJudge(MagicMock())

        # Test ISO format with Z
        dt = judge._parse_qoj_time("2024-06-02T21:00:00Z")
        assert dt is not None
        assert dt.month == 6
        assert dt.day == 2
        assert dt.hour == 21

        # Test simple format
        dt = judge._parse_qoj_time("2024-06-02 12:00:00")
        assert dt is not None
        assert dt.hour == 12

    def test_crawl_user_submissions_mocked(self):
        """Test crawling submissions with mocked HTML response"""
        # Sample HTML table for submissions
        html_content = """
        <html>
        <body>
        <table>
            <tbody>
                <tr>
                    <td><a href="/submission/123456">123456</a></td>
                    <td>2024-06-02 21:00:00</td>
                    <td><a href="/problem/1">1. A + B Problem</a></td>
                    <td>Accepted</td>
                    <td>Python</td>
                    <td>100</td>
                </tr>
                <tr>
                    <td><a href="/submission/123457">123457</a></td>
                    <td>2024-06-02 22:00:00</td>
                    <td><a href="/problem/2">2. Another Problem</a></td>
                    <td>Wrong Answer</td>
                    <td>Python</td>
                    <td>0</td>
                </tr>
            </tbody>
        </table>
        </body>
        </html>
        """

        mock_crawler = MagicMock()
        mock_crawler.get_page_content = MagicMock(return_value=html_content)

        judge = QojJudge(MagicMock())
        judge._get_browser = MagicMock(return_value=mock_crawler)

        user_judge = make_user_judge()
        from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)

        submissions = judge.crawl_user_submissions(user_judge, from_timestamp)

        assert len(submissions) == 2
        assert submissions[0].submission_id == "123456"
        assert submissions[0].exercise.code == "1"
        assert submissions[0].verdict == Verdict.AC
        assert submissions[0].points == 100

        assert submissions[1].submission_id == "123457"
        assert submissions[1].exercise.code == "2"
        assert submissions[1].verdict == Verdict.WA
        assert submissions[1].points == 0

    def test_crawl_user_submissions_with_timestamp_filter(self):
        """Test that timestamp filtering works"""
        html_content = """
        <html>
        <body>
        <table>
            <tbody>
                <tr>
                    <td><a href="/submission/123456">123456</a></td>
                    <td>2024-06-01 10:00:00</td>
                    <td><a href="/problem/1">1. A + B Problem</a></td>
                    <td>Accepted</td>
                    <td>Python</td>
                    <td>100</td>
                </tr>
                <tr>
                    <td><a href="/submission/123457">123457</a></td>
                    <td>2024-06-02 22:00:00</td>
                    <td><a href="/problem/2">2. Another Problem</a></td>
                    <td>Accepted</td>
                    <td>Python</td>
                    <td>100</td>
                </tr>
            </tbody>
        </table>
        </body>
        </html>
        """

        mock_crawler = MagicMock()
        mock_crawler.get_page_content = MagicMock(return_value=html_content)

        judge = QojJudge(MagicMock())
        judge._get_browser = MagicMock(return_value=mock_crawler)

        user_judge = make_user_judge()
        # Only get submissions after 2024-06-01 12:00:00
        from_timestamp = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

        submissions = judge.crawl_user_submissions(user_judge, from_timestamp)

        # Only the second submission should be returned
        assert len(submissions) == 1
        assert submissions[0].submission_id == "123457"