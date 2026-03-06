import uuid
from uuid import UUID

import pytest
from sqlalchemy import Engine

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.oj.db.repositories.judge import AbstractExerciseRepository
from hjudge.oj.db.repositories.submission import AbstractSubmissionRepository
from hjudge.oj.db.tables import exercise_table, submission_table
from hjudge.oj.models.judge import Exercise, JudgeEnum
from hjudge.oj.models.submission import Submission, Verdict
from tests.conftest import engine


@pytest.fixture(autouse=True)
def clear_tables(engine: Engine):
    with engine.connect() as connection:
        connection.execute(exercise_table.delete())
        connection.execute(submission_table.delete())
        connection.commit()


def test_add_and_get_an_exercise(uow: AbstractUnitOfWork):
    exercise = Exercise(judge=JudgeEnum.CODEFORCES, code="1234A", title="abcd")
    with uow:
        exercise_repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright:ignore
        exercise_repo.add_exercise(exercise)
        uow.commit()
    result = exercise_repo.get_exercise(exercise.id)
    assert result == exercise


def test_add_and_get_an_submission(uow: AbstractUnitOfWork):
    # with
    exercise = Exercise(judge=JudgeEnum.CODEFORCES, code="1234A", title="abcd")
    with uow:
        exercise_repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright:ignore
        exercise_repo.add_exercise(exercise)
    # and
    user_id = uuid.uuid4()
    submission = Submission(exercise=exercise, user=user_id, verdict=Verdict.AC)
    # act
    with uow:
        submission_repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright:ignore
        submission_repo.add_submission(submission)
        uow.commit()
    # assert
    result = submission_repo.get_submission(submission.id)
    assert result == exercise


def test_get_submission_list(uow: AbstractUnitOfWork):
    # with
    exercise = Exercise(judge=JudgeEnum.CODEFORCES, code="1234A", title="abcd")
    with uow:
        exercise_repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright:ignore
        exercise_repo.add_exercise(exercise)
    # and
    user_id = uuid.uuid4()
    submissions = [
        Submission(exercise=exercise, user=user_id, verdict=Verdict.AC),
        Submission(exercise=exercise, user=user_id, verdict=Verdict.AC),
        Submission(exercise=exercise, user=user_id, verdict=Verdict.AC),
    ]
    # act
    with uow:
        submission_repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright:ignore
        for submission in submissions:
            submission_repo.add_submission(submission)
        uow.commit()
    # assert
    results = submission_repo.get_submissions_by_user_and_problem(
        user_id=user_id, exercise_id=exercise.id
    )
    results_submissions_id = {result.id: result for result in results}
    for submission in submissions:
        assert results_submissions_id[submission.id] == submission
