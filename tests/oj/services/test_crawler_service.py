import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from sqlalchemy import Engine

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.oj.db.entities.exercise import ExerciseEntity
from hjudge.oj.db.entities.user_judge import UserJudgeEntity
from hjudge.oj.db.repositories.exercise import AbstractExerciseRepository
from hjudge.oj.db.repositories.submission import AbstractSubmissionRepository
from hjudge.oj.db.repositories.user_judge import AbstractUserJudgeRepository
from hjudge.oj.db.tables import exercise_table, submission_table, user_judge_table
from hjudge.oj.models.judges import Exercise, JudgeEnum
from hjudge.oj.models.submission import Submission, Verdict
from hjudge.oj.models.user_judge import UserJudge

# Sample data
USER_ID_1 = uuid.uuid4()
USER_ID_2 = uuid.uuid4()
EXERCISE_1 = Exercise(judge=JudgeEnum.CODEFORCES, code="1234A", title="Problem A")
EXERCISE_2 = Exercise(judge=JudgeEnum.CODEFORCES, code="1234B", title="Problem B")

LATER_TIMESTAMP = datetime(2026, 3, 13, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def clear_tables(engine: Engine):
    """Clear all relevant tables before each test"""
    with engine.connect() as connection:
        connection.execute(submission_table.delete())
        connection.execute(user_judge_table.delete())
        connection.execute(exercise_table.delete())
        connection.commit()


@pytest.fixture(autouse=True)
def setup_data(uow: AbstractUnitOfWork):
    """Setup exercises and user_judges before each test"""
    with uow:
        # Add exercises
        exercise_repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        exercise_repo.add_exercise(ExerciseEntity.from_model(EXERCISE_1))
        exercise_repo.add_exercise(ExerciseEntity.from_model(EXERCISE_2))

        # Add user judges
        user_judge_repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        user_judge_1 = UserJudge(
            user_id=USER_ID_1,
            judge=JudgeEnum.CODEFORCES,
            handle="user1_cf",
        )
        user_judge_2 = UserJudge(
            user_id=USER_ID_2,
            judge=JudgeEnum.CODEFORCES,
            handle="user2_cf",
        )
        user_judge_repo.upsert(UserJudgeEntity.from_model(user_judge_1))
        user_judge_repo.upsert(UserJudgeEntity.from_model(user_judge_2))

        uow.commit()


@pytest.mark.asyncio
async def test_crawl_all_users(uow: AbstractUnitOfWork):
    """Test that crawler fetches submissions for all users"""
    from hjudge.oj.services.crawler import crawl_all_users

    # Mock the judge factory and judge
    mock_judge = MagicMock()
    mock_judge.crawl_user_submissions = AsyncMock(return_value=[
        Submission(
            exercise=EXERCISE_1,
            user_id=USER_ID_1,
            verdict=Verdict.AC,
            submission_id="sub1",
            submitted_at=datetime(2026, 3, 13, 10, 0, 0, tzinfo=timezone.utc),
        ),
        Submission(
            exercise=EXERCISE_2,
            user_id=USER_ID_1,
            verdict=Verdict.WA,
            submission_id="sub2",
            submitted_at=datetime(2026, 3, 13, 11, 0, 0, tzinfo=timezone.utc),
        ),
    ])
    mock_judge.__aenter__ = AsyncMock(return_value=mock_judge)
    mock_judge.__aexit__ = AsyncMock(return_value=None)

    mock_judge_factory = MagicMock()
    mock_judge_factory.create_from.return_value = mock_judge

    # act
    await crawl_all_users(uow, mock_judge_factory)

    # assert - judge was called for each user
    assert mock_judge.crawl_user_submissions.call_count == 2

    # assert - submissions were inserted
    with uow:
        submission_repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright: ignore
        submissions = submission_repo.get_submissions_by_exercise_and_user(
            EXERCISE_1.id, USER_ID_1
        )
        assert len(submissions) == 1
        uow.rollback()


@pytest.mark.asyncio
async def test_crawl_updates_last_crawled(uow: AbstractUnitOfWork):
    """Test that crawler updates last_crawled timestamp"""
    from hjudge.oj.services.crawler import crawl_all_users

    # Mock the judge to return submissions with specific timestamps
    mock_judge = MagicMock()
    mock_judge.crawl_user_submissions = AsyncMock(return_value=[
        Submission(
            exercise=EXERCISE_1,
            user_id=USER_ID_1,
            verdict=Verdict.AC,
            submission_id="sub1",
            submitted_at=datetime(2026, 3, 13, 10, 0, 0, tzinfo=timezone.utc),
        ),
        Submission(
            exercise=EXERCISE_2,
            user_id=USER_ID_1,
            verdict=Verdict.WA,
            submission_id="sub2",
            submitted_at=datetime(2026, 3, 13, 15, 0, 0, tzinfo=timezone.utc),  # Latest
        ),
    ])
    mock_judge.__aenter__ = AsyncMock(return_value=mock_judge)
    mock_judge.__aexit__ = AsyncMock(return_value=None)

    mock_judge_factory = MagicMock()
    mock_judge_factory.create_from.return_value = mock_judge

    # act
    await crawl_all_users(uow, mock_judge_factory)

    # assert - last_crawled should be updated to latest submission time
    with uow:
        user_judge_repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        user_judge = user_judge_repo.get_by_user_and_judge(USER_ID_1, JudgeEnum.CODEFORCES)
        assert user_judge is not None
        # SQLite stores datetimes without timezone, so compare naive datetimes
        assert user_judge.last_crawled.replace(tzinfo=None) == datetime(
            2026, 3, 13, 15, 0, 0
        )
        uow.rollback()


@pytest.mark.asyncio
async def test_crawl_handles_new_exercise(uow: AbstractUnitOfWork):
    """Test that crawler creates new exercises when needed"""
    from hjudge.oj.services.crawler import crawl_all_users

    # Mock submission with new exercise
    new_exercise = Exercise(judge=JudgeEnum.CODEFORCES, code="9999Z", title="New Problem")
    mock_judge = MagicMock()
    mock_judge.crawl_user_submissions = AsyncMock(return_value=[
        Submission(
            exercise=new_exercise,
            user_id=USER_ID_1,
            verdict=Verdict.AC,
            submission_id="sub_new",
            submitted_at=datetime(2026, 3, 13, 10, 0, 0, tzinfo=timezone.utc),
        ),
    ])
    mock_judge.crawl_exercises_batch = AsyncMock(return_value=[new_exercise])
    mock_judge.get_batch_config.return_value = {"url": "test", "contest": "9999"}
    mock_judge.__aenter__ = AsyncMock(return_value=mock_judge)
    mock_judge.__aexit__ = AsyncMock(return_value=None)

    mock_judge_factory = MagicMock()
    mock_judge_factory.create_from.return_value = mock_judge

    # act
    await crawl_all_users(uow, mock_judge_factory)

    # assert - new exercise should be created
    with uow:
        exercise_repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        result = exercise_repo.get_exercise_by_judge_and_code(
            JudgeEnum.CODEFORCES, "9999Z"
        )
        assert result is not None
        uow.rollback()


@pytest.mark.asyncio
async def test_crawl_skips_duplicates(uow: AbstractUnitOfWork):
    """Test that crawler skips duplicate submissions"""
    from hjudge.oj.services.crawler import crawl_all_users

    # First crawl - insert initial submission
    mock_judge = MagicMock()
    mock_judge.crawl_user_submissions = AsyncMock(return_value=[
        Submission(
            exercise=EXERCISE_1,
            user_id=USER_ID_1,
            verdict=Verdict.AC,
            submission_id="sub1",
            submitted_at=datetime(2026, 3, 13, 10, 0, 0, tzinfo=timezone.utc),
        ),
    ])
    mock_judge.__aenter__ = AsyncMock(return_value=mock_judge)
    mock_judge.__aexit__ = AsyncMock(return_value=None)

    mock_judge_factory = MagicMock()
    mock_judge_factory.create_from.return_value = mock_judge

    await crawl_all_users(uow, mock_judge_factory)

    # Second crawl - try to insert same submission again
    mock_judge.crawl_user_submissions = AsyncMock(return_value=[
        Submission(
            exercise=EXERCISE_1,
            user_id=USER_ID_1,
            verdict=Verdict.WA,  # Different verdict, same submission_id
            submission_id="sub1",  # Duplicate!
            submitted_at=datetime(2026, 3, 13, 11, 0, 0, tzinfo=timezone.utc),
        ),
        Submission(
            exercise=EXERCISE_2,
            user_id=USER_ID_1,
            verdict=Verdict.AC,
            submission_id="sub2",  # New
            submitted_at=datetime(2026, 3, 13, 12, 0, 0, tzinfo=timezone.utc),
        ),
    ])

    await crawl_all_users(uow, mock_judge_factory)

    # assert - should only have 2 submissions (sub1 from first crawl, sub2 from second)
    with uow:
        submission_repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright: ignore
        user1_submissions = submission_repo.get_submissions_by_exercise_and_user(
            EXERCISE_1.id, USER_ID_1
        )
        assert len(user1_submissions) == 1  # Still only 1, duplicate was skipped
        assert user1_submissions[0].verdict == Verdict.AC  # Original verdict preserved
        uow.rollback()