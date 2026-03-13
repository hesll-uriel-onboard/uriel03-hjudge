from datetime import datetime, timezone
from uuid import UUID

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.oj.db.entities.exercise import ExerciseEntity
from hjudge.oj.db.entities.submission import SubmissionEntity
from hjudge.oj.db.repositories.exercise import AbstractExerciseRepository
from hjudge.oj.db.repositories.submission import AbstractSubmissionRepository
from hjudge.oj.db.repositories.user_judge import AbstractUserJudgeRepository
from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.judges.factory import JudgeFactory
from hjudge.oj.models.user_judge import UserJudge


def crawl_all_users(uow: AbstractUnitOfWork, judge_factory: JudgeFactory) -> None:
    """Crawl submissions for all UserJudge entries.

    For each UserJudge:
    1. Get judge instance from factory
    2. Call crawl_user_submissions with the UserJudge
    3. For each submission, ensure exercise exists
    4. Batch insert submissions (dedup happens in repo)
    5. Update last_crawled timestamp
    """
    with uow:
        # Create repositories
        user_judge_repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        exercise_repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        submission_repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright: ignore

        # Get all UserJudge entries
        user_judge_entities = user_judge_repo.list_all()
        user_judges = [e.as_model() for e in user_judge_entities]

        # For each UserJudge, crawl submissions
        for user_judge in user_judges:
            judge = judge_factory.create_from(user_judge.judge)

            # Handle timezone-naive last_crawled from database
            last_crawled = user_judge.last_crawled
            if last_crawled.tzinfo is None:
                last_crawled = last_crawled.replace(tzinfo=timezone.utc)

            submissions = judge.crawl_user_submissions(user_judge, last_crawled)

            if not submissions:
                continue

            # Track the latest timestamp for updating last_crawled
            latest_timestamp = last_crawled
            entities = []

            for submission in submissions:
                # Ensure exercise exists
                exercise_entity = exercise_repo.get_exercise_by_judge_and_code(
                    submission.exercise.judge, submission.exercise.code
                )

                if exercise_entity is None:
                    # Create new exercise
                    exercise_entity = ExerciseEntity(
                        judge=submission.exercise.judge,
                        code=submission.exercise.code,
                        title=submission.exercise.title,
                    )
                    exercise_repo.add_exercise(exercise_entity)

                # Create submission entity
                # Note: We need to flush to get the exercise id if newly created
                submission_entity = SubmissionEntity(
                    exercise_id=exercise_entity.id,
                    user_id=submission.user_id,
                    verdict=submission.verdict,
                    submission_id=submission.submission_id,
                    submitted_at=submission.submitted_at,
                    content=submission.content,
                    points=submission.points,
                )
                entities.append(submission_entity)

                # Track latest timestamp (ensure both are timezone-aware)
                submitted_at = submission.submitted_at
                if submitted_at.tzinfo is None:
                    submitted_at = submitted_at.replace(tzinfo=timezone.utc)
                if submitted_at > latest_timestamp:
                    latest_timestamp = submitted_at

            # Batch insert submissions (dedup happens in repo)
            if entities:
                submission_repo.add_submissions_batch(entities)

            # Update last_crawled to timestamp of latest submission
            if latest_timestamp > last_crawled:
                # Get the entity id from the original list
                entity = user_judge_repo.get_by_user_and_judge(
                    user_judge.user_id, user_judge.judge
                )
                if entity:
                    user_judge_repo.update_last_crawled(entity.id, latest_timestamp)

        uow.commit()