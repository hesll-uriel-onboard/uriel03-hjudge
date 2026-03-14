import uuid
from datetime import datetime

import pytest
from sqlalchemy import Engine

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.oj.db.entities.exercise import ExerciseEntity
from hjudge.oj.db.entities.submission import SubmissionEntity
from hjudge.oj.db.repositories.exercise import AbstractExerciseRepository
from hjudge.oj.db.repositories.submission import AbstractSubmissionRepository
from hjudge.oj.db.tables import exercise_table, submission_table
from hjudge.oj.models.judges import Exercise, JudgeEnum
from hjudge.oj.models.submission import Submission, Verdict

# Sample data
USER_ID_1 = uuid.uuid4()
USER_ID_2 = uuid.uuid4()
EXERCISE_1 = Exercise(judge=JudgeEnum.CODEFORCES, code="1234A", title="Problem A")
EXERCISE_2 = Exercise(judge=JudgeEnum.CODEFORCES, code="1234B", title="Problem B")


@pytest.fixture(autouse=True)
def clear_and_setup_tables(engine: Engine, uow: AbstractUnitOfWork):
    """Clear tables and setup exercises before each test"""
    with engine.connect() as connection:
        connection.execute(submission_table.delete())
        connection.execute(exercise_table.delete())
        connection.commit()

    # Setup exercises
    with uow:
        repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        repo.add_exercise(ExerciseEntity.from_model(EXERCISE_1))
        repo.add_exercise(ExerciseEntity.from_model(EXERCISE_2))
        uow.commit()


def test_add_submissions_batch(uow: AbstractUnitOfWork):
    # with
    submissions = [
        Submission(
            exercise=EXERCISE_1,
            user_id=USER_ID_1,
            verdict=Verdict.AC,
            submission_id="sub1",
            submitted_at=datetime(2026, 3, 13, 10, 0, 0),
        ),
        Submission(
            exercise=EXERCISE_1,
            user_id=USER_ID_1,
            verdict=Verdict.WA,
            submission_id="sub2",
            submitted_at=datetime(2026, 3, 13, 10, 5, 0),
        ),
        Submission(
            exercise=EXERCISE_2,
            user_id=USER_ID_1,
            verdict=Verdict.AC,
            submission_id="sub3",
            submitted_at=datetime(2026, 3, 13, 10, 10, 0),
        ),
    ]

    # act
    with uow:
        repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright: ignore
        inserted = repo.add_submissions_batch(
            [SubmissionEntity.from_model(s) for s in submissions]
        )
        uow.commit()

    # assert - all 3 should be inserted
    assert len(inserted) == 3

    with uow:
        repo = uow.create_repository(AbstractSubmissionRepository)  # pyright: ignore
        result = repo.get_submissions_by_exercise_and_user(EXERCISE_1.id, USER_ID_1)
        assert len(result) == 2
        uow.rollback()


def test_add_submissions_batch_with_duplicates(uow: AbstractUnitOfWork):
    # with - insert initial batch
    initial_submissions = [
        Submission(
            exercise=EXERCISE_1,
            user_id=USER_ID_1,
            verdict=Verdict.AC,
            submission_id="sub1",
            submitted_at=datetime(2026, 3, 13, 10, 0, 0),
        ),
    ]

    with uow:
        repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright: ignore
        repo.add_submissions_batch(
            [SubmissionEntity.from_model(s) for s in initial_submissions]
        )
        uow.commit()

    # act - try to insert batch with duplicate submission_id
    new_submissions = [
        Submission(
            exercise=EXERCISE_1,
            user_id=USER_ID_1,
            verdict=Verdict.WA,  # Different verdict, same submission_id
            submission_id="sub1",  # Duplicate!
            submitted_at=datetime(2026, 3, 13, 10, 5, 0),
        ),
        Submission(
            exercise=EXERCISE_2,
            user_id=USER_ID_1,
            verdict=Verdict.AC,
            submission_id="sub2",  # New
            submitted_at=datetime(2026, 3, 13, 10, 10, 0),
        ),
    ]

    with uow:
        repo = uow.create_repository(AbstractSubmissionRepository)  # pyright: ignore
        inserted = repo.add_submissions_batch(
            [SubmissionEntity.from_model(s) for s in new_submissions]
        )
        uow.commit()

        # assert - only the new one should be inserted (inside session)
        assert len(inserted) == 1
        assert inserted[0].submission_id == "sub2"


def test_add_submissions_batch_empty(uow: AbstractUnitOfWork):
    # act
    with uow:
        repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright: ignore
        inserted = repo.add_submissions_batch([])
        uow.commit()

    # assert
    assert len(inserted) == 0


def test_add_submissions_batch_multiple_users(uow: AbstractUnitOfWork):
    # with
    submissions = [
        Submission(
            exercise=EXERCISE_1,
            user_id=USER_ID_1,
            verdict=Verdict.AC,
            submission_id="user1_sub1",
            submitted_at=datetime(2026, 3, 13, 10, 0, 0),
        ),
        Submission(
            exercise=EXERCISE_1,
            user_id=USER_ID_2,
            verdict=Verdict.AC,
            submission_id="user2_sub1",
            submitted_at=datetime(2026, 3, 13, 10, 0, 0),
        ),
    ]

    # act
    with uow:
        repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright: ignore
        inserted = repo.add_submissions_batch(
            [SubmissionEntity.from_model(s) for s in submissions]
        )
        uow.commit()

    # assert
    assert len(inserted) == 2

    # Verify each user has their submission
    with uow:
        repo = uow.create_repository(AbstractSubmissionRepository)  # pyright: ignore
        user1_subs = repo.get_submissions_by_exercise_and_user(EXERCISE_1.id, USER_ID_1)
        user2_subs = repo.get_submissions_by_exercise_and_user(EXERCISE_1.id, USER_ID_2)
        uow.rollback()

    assert len(user1_subs) == 1
    assert len(user2_subs) == 1