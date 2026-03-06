import pytest
from sqlalchemy import Engine

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.oj.db.entities.exercise import ExerciseEntity
from hjudge.oj.db.repositories.exercise import AbstractExerciseRepository
from hjudge.oj.db.tables import exercise_table, submission_table
from hjudge.oj.models.exercise import Exercise, JudgeEnum


@pytest.fixture(autouse=True)
def clear_tables(engine: Engine):
    with engine.connect() as connection:
        connection.execute(exercise_table.delete())
        connection.execute(submission_table.delete())
        connection.commit()


def test_add_and_get_exercise(uow: AbstractUnitOfWork):
    # with
    exercise = Exercise(judge=JudgeEnum.CODEFORCES, code="1234A", title="def")
    # act
    with uow:
        repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        repo.add_exercise(ExerciseEntity.from_model(exercise))
        uow.commit()
    # act 2 and assert
    with uow:
        repo = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        result = repo.get_exercise(exercise.id)
        assert result is not None
        result = result.as_model()
        uow.commit()
    assert result == exercise
