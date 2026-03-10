from typing import List
from uuid import UUID

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.oj.db.entities.submission import SubmissionEntity
from hjudge.oj.db.repositories import exercise
from hjudge.oj.db.repositories.exercise import AbstractExerciseRepository
from hjudge.oj.db.repositories.submission import AbstractSubmissionRepository
from hjudge.oj.errors import ExerciseNotFoundError, SubmissionNotFoundError
from hjudge.oj.models.submission import Submission, Verdict


def submit(
    user_id: UUID, exercise_id: UUID, verdict: Verdict, uow: AbstractUnitOfWork
) -> Submission:
    with uow:
        exercise_repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        submission_repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright: ignore

        entity = exercise_repo.get_exercise(exercise_id)
        if entity is None:
            raise ExerciseNotFoundError

        submission = Submission(
            exercise=entity.as_model(), user_id=user_id, verdict=verdict
        )
        submission_repo.add_submission(SubmissionEntity.from_model(submission))
        uow.commit()
    return submission


def get_submissions(
    user_id: UUID, exercise_id: UUID, uow: AbstractUnitOfWork
) -> List[Submission]:
    with uow:
        submission_repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright: ignore

        entities = submission_repo.get_submissions_by_exercise_and_user(
            exercise_id=exercise_id, user_id=user_id
        )
        if entities is None:
            raise SubmissionNotFoundError

        submissions = [entity.as_model() for entity in entities]
        uow.rollback()
    return submissions
