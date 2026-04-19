import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

import pytest

from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.judges.lqdoj import LqdojJudge, LqdojExercise, LQDOJ_VERDICT_MAP
from hjudge.oj.models.submission import Verdict
from hjudge.oj.models.user_judge import UserJudge

# Test user ID
USER_ID = uuid.uuid4()


def make_user_judge(handle: str = "testuser") -> UserJudge:
    """Helper to create a UserJudge for testing"""
    return UserJudge(
        user_id=USER_ID,
        judge=JudgeEnum.LQDOJ,
        handle=handle,
    )


class TestLqdojExercise:
    """Tests for LqdojExercise class"""

    def test_create_from(self):
        data = {
            "code": "aplusb",
            "name": "A Plus B",
        }
        exercise = LqdojExercise.create_from(data)
        assert exercise.code == "aplusb"
        assert exercise.title == "A Plus B"
        assert exercise.judge == JudgeEnum.LQDOJ

    def test_create_from_empty_title(self):
        data = {
            "code": "testprob",
        }
        exercise = LqdojExercise.create_from(data)
        assert exercise.code == "testprob"
        assert exercise.title == ""

    def test_init(self):
        exercise = LqdojExercise("aplusb", "A Plus B")
        assert exercise.code == "aplusb"
        assert exercise.title == "A Plus B"
        assert exercise.judge == JudgeEnum.LQDOJ


class TestLqdojJudge:
    """Tests for LqdojJudge class"""

    def test_get_exercise_url(self):
        judge = LqdojJudge(MagicMock())
        url = judge.get_exercise_url("aplusb")
        assert url == "https://lqdoj.edu.vn/problem/aplusb"

    def test_get_submission_url(self):
        judge = LqdojJudge(MagicMock())
        url = judge.get_submission_url("123456")
        assert url == "https://lqdoj.edu.vn/submission/123456"

    def test_verdict_mapping(self):
        """Test that LQDOJ verdicts map correctly to our Verdict enum"""
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
            ("SC", Verdict.WA),
        ]

        for lqdoj_verdict, expected_verdict in test_cases:
            assert LQDOJ_VERDICT_MAP.get(lqdoj_verdict) == expected_verdict

    @pytest.mark.asyncio
    async def test_crawl_exercises_batch(self):
        """Test crawling exercise info from LQDOJ problem page"""
        html_content = """
        <html>
        <body>
        <div class="problem-title">
            <h2 class="title-row">A cộng B</h2>
        </div>
        </body>
        </html>
        """

        mock_browser = MagicMock()
        mock_browser.get_page_content = AsyncMock(return_value=html_content)

        judge = LqdojJudge(MagicMock())
        judge._browser = mock_browser

        exercises = list(await judge.crawl_exercises_batch(code="aplusb"))

        assert len(exercises) == 1
        assert exercises[0].code == "aplusb"
        assert exercises[0].title == "A cộng B"
        assert exercises[0].judge == JudgeEnum.LQDOJ

    @pytest.mark.asyncio
    async def test_crawl_user_submissions_mocked(self):
        """Test crawling submissions with mocked HTML response"""
        html_content = """
        <html>
        <body>
        <div id="submissions-table">
            <div class="submission-row" id="8292705">
                <div class="sub-problem"><a href="/problem/tjalg">Tìm thành phần liên thông mạnh</a></div>
                <div class="state WA"><span class="status">WA</span></div>
                <span class="time-with-rel" data-iso="2025-01-27T10:00:00+00:00">2 days ago</span>
            </div>
            <div class="submission-row" id="8292706">
                <div class="sub-problem"><a href="/problem/aplusb">A cộng B</a></div>
                <div class="state AC"><span class="status">AC</span></div>
                <span class="time-with-rel" data-iso="2025-01-27T11:00:00+00:00">1 day ago</span>
            </div>
            <div class="submission-row" id="8292707">
                <div class="sub-problem"><a href="/problem/testprob">Test Problem</a></div>
                <div class="state TLE"><span class="status">TLE</span></div>
                <span class="time-with-rel" data-iso="2025-01-27T12:00:00+00:00">12 hours ago</span>
            </div>
        </div>
        <ul class="pagination">
            <li><a href="?page=1">1</a></li>
            <li><a href="?page=2">2</a></li>
        </ul>
        </body>
        </html>
        """

        mock_browser = MagicMock()
        mock_browser.get_page_content = AsyncMock(return_value=html_content)

        judge = LqdojJudge(MagicMock())
        judge._browser = mock_browser

        user_judge = make_user_judge()
        from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)

        submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

        assert len(submissions) == 3
        assert submissions[0].submission_id == "8292705"
        assert submissions[0].exercise.code == "tjalg"
        assert submissions[0].verdict == Verdict.WA
        assert submissions[0].user_id == USER_ID
        assert submissions[0].points == 0

        assert submissions[1].submission_id == "8292706"
        assert submissions[1].exercise.code == "aplusb"
        assert submissions[1].verdict == Verdict.AC
        assert submissions[1].points == 100

        assert submissions[2].submission_id == "8292707"
        assert submissions[2].exercise.code == "testprob"
        assert submissions[2].verdict == Verdict.TLE

    @pytest.mark.asyncio
    async def test_crawl_user_submissions_with_timestamp_filter(self):
        """Test that timestamp filtering works"""
        html_content = """
        <html>
        <body>
        <div id="submissions-table">
            <div class="submission-row" id="100">
                <div class="sub-problem"><a href="/problem/aplusb">A cộng B</a></div>
                <div class="state AC"><span class="status">AC</span></div>
                <span class="time-with-rel" data-iso="2025-01-27T10:00:00+00:00">2 days ago</span>
            </div>
            <div class="submission-row" id="101">
                <div class="sub-problem"><a href="/problem/testprob">Test Problem</a></div>
                <div class="state AC"><span class="status">AC</span></div>
                <span class="time-with-rel" data-iso="2025-01-28T10:00:00+00:00">1 day ago</span>
            </div>
        </div>
        </body>
        </html>
        """

        mock_browser = MagicMock()
        mock_browser.get_page_content = AsyncMock(return_value=html_content)

        judge = LqdojJudge(MagicMock())
        judge._browser = mock_browser

        user_judge = make_user_judge()

        # Only get submissions after 2025-01-27T12:00:00
        from_timestamp = datetime(2025, 1, 27, 12, 0, 0, tzinfo=timezone.utc)
        submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

        assert len(submissions) == 1
        assert submissions[0].submission_id == "101"

    @pytest.mark.asyncio
    async def test_crawl_user_submissions_empty(self):
        """Test crawling when there are no submissions"""
        html_content = """
        <html>
        <body>
        <div id="submissions-table">
        </div>
        </body>
        </html>
        """

        mock_browser = MagicMock()
        mock_browser.get_page_content = AsyncMock(return_value=html_content)

        judge = LqdojJudge(MagicMock())
        judge._browser = mock_browser

        user_judge = make_user_judge()
        from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)

        submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

        assert len(submissions) == 0

    @pytest.mark.asyncio
    async def test_crawl_user_submissions_verdict_filtering(self):
        """Test that unknown verdicts are skipped"""
        html_content = """
        <html>
        <body>
        <div id="submissions-table">
            <div class="submission-row" id="100">
                <div class="sub-problem"><a href="/problem/aplusb">A cộng B</a></div>
                <div class="state AC"><span class="status">AC</span></div>
                <span class="time-with-rel" data-iso="2025-01-27T10:00:00+00:00">2 days ago</span>
            </div>
            <div class="submission-row" id="101">
                <div class="sub-problem"><a href="/problem/aplusb">A cộng B</a></div>
                <div class="state UNKNOWN"><span class="status">UNKNOWN</span></div>
                <span class="time-with-rel" data-iso="2025-01-27T11:00:00+00:00">1 day ago</span>
            </div>
        </div>
        </body>
        </html>
        """

        mock_browser = MagicMock()
        mock_browser.get_page_content = AsyncMock(return_value=html_content)

        judge = LqdojJudge(MagicMock())
        judge._browser = mock_browser

        user_judge = make_user_judge()
        from_timestamp = datetime.fromtimestamp(0, tz=timezone.utc)

        submissions = await judge.crawl_user_submissions(user_judge, from_timestamp)

        # Only the AC submission should be returned
        assert len(submissions) == 1
        assert submissions[0].submission_id == "100"