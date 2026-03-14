import pytest
from sqlalchemy import Engine

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.oj.db.entities.exercise import ExerciseEntity
from hjudge.oj.db.repositories.exercise import AbstractExerciseRepository
from hjudge.oj.db.tables import exercise_table, submission_table
from hjudge.oj.models.judges import Exercise, JudgeEnum

exercises_list = [
    Exercise(judge=JudgeEnum.CODEFORCES, code=prob, title=prob)
    for prob in ["abc", "def", "ghi", "jkl", "mno"]
]


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


def test_add_batch(uow: AbstractUnitOfWork):
    # act
    with uow:
        repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        repo.add_exercises(
            [ExerciseEntity.from_model(exercise) for exercise in exercises_list]
        )
        uow.commit()
    # assert
    with uow:
        repo = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        for exercise in exercises_list:
            result = repo.get_exercise_by_judge_and_code(
                exercise.judge, exercise.code
            )
            assert result is not None
            assert result.judge == exercise.judge
            assert result.code == exercise.code
            assert result.title == exercise.title
        uow.rollback()


def test_add_batch_with_duplication(uow: AbstractUnitOfWork):
    one = exercises_list[:3]
    two = exercises_list[1:]
    # with
    with uow:
        repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        repo.add_exercises(
            [ExerciseEntity.from_model(exercise) for exercise in one]
        )
        uow.commit()
    # act
    with uow:
        repo = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        repo.add_exercises(
            [ExerciseEntity.from_model(exercise) for exercise in two]
        )
        uow.commit()
    # assert
    with uow:
        repo = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        for exercise in exercises_list:
            result = repo.get_exercise_by_judge_and_code(
                exercise.judge, exercise.code
            )
            assert result is not None
            assert result.judge == exercise.judge
            assert result.code == exercise.code
            assert result.title == exercise.title
        uow.rollback()
