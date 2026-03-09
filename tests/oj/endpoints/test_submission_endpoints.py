import json
import uuid

import pytest
from litestar.app import Litestar
from litestar.testing import TestClient
from sqlalchemy import Engine

from hjudge.commons.db.uow import AbstractExerciseRepository, AbstractUnitOfWork
from hjudge.oj.db.entities.exercise import ExerciseEntity
from hjudge.oj.db.tables import exercise_table, submission_table
from hjudge.oj.models.judges import Exercise, JudgeEnum
from hjudge.oj.models.submission import Verdict

exercise = Exercise(judge=JudgeEnum.CODEFORCES, code="abc")
user_id = uuid.uuid4()

JSON_ENCODER = json.JSONEncoder()


def build_submission(
    exercise_id: uuid.UUID, user_id: uuid.UUID, verdict: Verdict
) -> str:
    return JSON_ENCODER.encode(
        {"exercise": str(exercise_id), "user": str(user_id), "verdict": str(verdict)}
    )


@pytest.fixture(autouse=True)
def clear_tables(uow: AbstractUnitOfWork):
    with uow:
        uow.execute(submission_table.delete())
        uow.execute(exercise_table.delete())

        exercise_repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        exercise_repo.add_exercise(ExerciseEntity.from_model(exercise))

        uow.commit()


def find_exercise(uow: AbstractUnitOfWork, exercise: Exercise) -> uuid.UUID:
    with uow:
        repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright:ignore
        result = repo.get_exercise_by_judge_and_code(
            exercise.judge, exercise.code
        )
        assert result is not None
        uow.commit()
        return result.as_model().id


def test_submit_normally(app: Litestar, uow: AbstractUnitOfWork):
    with TestClient(app) as client:
        exercise_id = find_exercise(uow, exercise)
        client.post(
            "/submissions",
            content=build_submission(exercise_id, user_id, Verdict.AC),
        )
        
