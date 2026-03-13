import json
import uuid
from datetime import datetime

import pytest
from litestar.app import Litestar
from litestar.testing import TestClient

from hjudge.commons.db.uow import AbstractExerciseRepository, AbstractUnitOfWork
from hjudge.oj.db.entities.exercise import ExerciseEntity
from hjudge.oj.db.entities.submission import SubmissionEntity
from hjudge.oj.db.repositories.submission import AbstractSubmissionRepository
from hjudge.oj.db.tables import exercise_table, submission_table
from hjudge.oj.models.judges import Exercise, JudgeEnum
from hjudge.oj.models.submission import Submission, Verdict

exercises = [
    Exercise(judge=JudgeEnum.CODEFORCES, code=code)
    for code in ["abc", "def", "ghi"]
]
verdicts = ["AC", "RTE", "WA"]
DEFAULT_USER_ID = uuid.uuid4()
___submissions = [
    [(exercise, DEFAULT_USER_ID, verdict) for verdict in verdicts]
    for exercise in exercises
]
submissions: list[tuple[Exercise, uuid.UUID, str]] = []
for _ in ___submissions:
    submissions += _

JSON_ENCODER = json.JSONEncoder()


def build_submission(
    exercise_id: uuid.UUID, user_id: uuid.UUID, verdict: str
) -> str:
    return JSON_ENCODER.encode(
        {
            "exercise_id": str(exercise_id),
            "user_id": str(user_id),
            "verdict": verdict,
        }
    )


@pytest.fixture(autouse=True)
def clear_tables(uow: AbstractUnitOfWork):
    with uow:
        uow.execute(submission_table.delete())
        uow.execute(exercise_table.delete())

        exercise_repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        for exercise in exercises:
            exercise_repo.add_exercise(ExerciseEntity.from_model(exercise))

        uow.commit()


def find_exercise(uow: AbstractUnitOfWork, exercise: Exercise) -> uuid.UUID:
    repo: AbstractExerciseRepository = uow.create_repository(
        AbstractExerciseRepository
    )  # pyright:ignore
    result = repo.get_exercise_by_judge_and_code(exercise.judge, exercise.code)
    assert result is not None
    return result.as_model().id


def test_submit(app: Litestar, uow: AbstractUnitOfWork):
    with TestClient(app) as client:
        for exercise, user_id, verdict in submissions:
            with uow:
                exercise_id = find_exercise(uow, exercise)
                uow.commit()

            response = client.post(
                "/api/submissions",
                content=build_submission(exercise_id, user_id, verdict),
            )
            assert response is not None
            assert response.status_code == 200
            submit_result = json.JSONDecoder().decode(response.content.decode())
            assert submit_result["exercise"]["id"] == str(exercise_id)
            assert submit_result["user_id"] == str(user_id)
            assert submit_result["verdict"] == verdict


def test_submission(app: Litestar, uow: AbstractUnitOfWork):
    with uow:
        submission_repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright: ignore
        for idx, (exercise, user_id, verdict) in enumerate(submissions):
            submission_repo.add_submission(
                SubmissionEntity.from_model(
                    Submission(
                        exercise=exercise,
                        user_id=user_id,
                        verdict=Verdict[verdict],
                        submission_id=f"sub_{idx}",
                    )
                )
            )
        uow.commit()

    with TestClient(app) as client:
        for exercise in exercises:
            response = client.get(
                f"/api/submissions?user={DEFAULT_USER_ID}&exercise={exercise.id}"
            )
            assert response is not None
            assert response.status_code == 200
            submissions_result: list[dict] = json.JSONDecoder().decode(
                response.content.decode()
            )
            assert isinstance(submissions_result, list)
            assert len(submissions_result) == 3
            verdicts = set()
            for submission in submissions_result:
                verdicts.add(submission["verdict"])
                assert submission["user_id"] == str(DEFAULT_USER_ID)
                assert submission["exercise"]["id"] == str(exercise.id)
            for x in verdicts:
                assert x in verdicts


def test_submit_not_found(app: Litestar):
    with TestClient(app) as client:
        response = client.post(
            "/api/submissions",
            content="""{
                "exercise_id":"81fbd94c-ce53-4ea9-ad8f-61613dbf6106",
                "user_id": "81fbd94c-ce53-4ea9-ad8f-61613dbf6106",
                "verdict": "AC"
            }""",
        )
        assert response.status_code == 404


def test_submission_not_found(app: Litestar):
    with TestClient(app) as client:
        response = client.get(
            "/api/submissions?user=81fbd94c-ce53-4ea9-ad8f-61613dbf6106&exercise=81fbd94c-ce53-4ea9-ad8f-61613dbf6106",
        )
        assert response.status_code == 200
        result = json.JSONDecoder().decode(response.content.decode())
        assert isinstance(result, list)
        assert len(result) == 0
