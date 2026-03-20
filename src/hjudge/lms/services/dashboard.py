"""Dashboard service for progress tracking and leaderboards."""

from uuid import UUID

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.db.repositories.course import (
    AbstractCourseRepository,
    AbstractLessonRepository,
)
from hjudge.lms.db.repositories.user import AbstractUserRepository
from hjudge.lms.models.dashboard import Leaderboard, ProgressEntry
from hjudge.lms.services import user as user_services
from hjudge.oj.db.repositories.submission import AbstractSubmissionRepository


def _get_user_by_id(user_id: UUID, uow: AbstractUnitOfWork):
    """Get user by ID assuming uow context is already active."""
    user_repo: AbstractUserRepository = uow.create_repository(
        AbstractUserRepository
    )  # pyright: ignore
    user_entity = user_repo.get_user_by_id(user_id)
    if user_entity is None:
        return None
    return user_entity.as_model()


def get_progress_for_lesson(
    user_id: UUID, lesson_id: UUID, uow: AbstractUnitOfWork
) -> ProgressEntry:
    """Get a user's progress for a specific lesson."""
    with uow:
        # Get lesson to find exercise IDs
        lesson_repo: AbstractLessonRepository = uow.create_repository(
            AbstractLessonRepository
        )  # pyright: ignore
        submission_repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright: ignore

        lesson_entity = lesson_repo.get_lesson(lesson_id)
        if lesson_entity is None:
            # Lesson not found - return empty progress
            user = _get_user_by_id(user_id, uow)
            if user is None:
                raise ValueError(f"User {user_id} not found")
            return ProgressEntry(user=user, total_points=0.0, breakdown={})

        lesson = lesson_entity.as_model()
        exercise_ids = lesson.exercise_ids

        if not exercise_ids:
            # No exercises - return empty progress
            user = _get_user_by_id(user_id, uow)
            if user is None:
                raise ValueError(f"User {user_id} not found")
            return ProgressEntry(user=user, total_points=0.0, breakdown={})

        # Get max points for each exercise
        max_points = submission_repo.get_max_points_by_exercise_and_user(
            exercise_ids, [user_id]
        )

        # Build breakdown and calculate total
        breakdown: dict[UUID, float] = {}
        total_points = 0.0

        for exercise_id in exercise_ids:
            points = max_points.get((exercise_id, user_id), 0)
            breakdown[exercise_id] = float(points)
            total_points += points

        # Scale to 0-100
        scaled_total = total_points / len(exercise_ids) if exercise_ids else 0.0

        user = _get_user_by_id(user_id, uow)
        if user is None:
            raise ValueError(f"User {user_id} not found")

        return ProgressEntry(user=user, total_points=scaled_total, breakdown=breakdown)


def get_progress_for_course(
    user_id: UUID, course_id: UUID, uow: AbstractUnitOfWork
) -> ProgressEntry:
    """Get a user's progress for a specific course."""
    with uow:
        lesson_repo: AbstractLessonRepository = uow.create_repository(
            AbstractLessonRepository
        )  # pyright: ignore

        # Get all lessons in the course
        lesson_entities = lesson_repo.list_lessons_by_course(course_id)
        lessons = [e.as_model() for e in lesson_entities]

        if not lessons:
            # No lessons - return empty progress
            user = _get_user_by_id(user_id, uow)
            if user is None:
                raise ValueError(f"User {user_id} not found")
            return ProgressEntry(user=user, total_points=0.0, breakdown={})

        # Calculate progress for each lesson
        breakdown: dict[UUID, float] = {}
        total_points = 0.0

        for lesson in lessons:
            # Calculate lesson progress inline to avoid nested context
            exercise_ids = lesson.exercise_ids
            if not exercise_ids:
                breakdown[lesson.id] = 0.0
                continue

            submission_repo: AbstractSubmissionRepository = uow.create_repository(
                AbstractSubmissionRepository
            )  # pyright: ignore
            max_points = submission_repo.get_max_points_by_exercise_and_user(
                exercise_ids, [user_id]
            )

            lesson_total = sum(max_points.get((eid, user_id), 0) for eid in exercise_ids)
            lesson_avg = lesson_total / len(exercise_ids)
            breakdown[lesson.id] = lesson_avg
            total_points += lesson_avg

        # Average across all lessons
        scaled_total = total_points / len(lessons) if lessons else 0.0

        user = _get_user_by_id(user_id, uow)
        if user is None:
            raise ValueError(f"User {user_id} not found")

        return ProgressEntry(user=user, total_points=scaled_total, breakdown=breakdown)


def get_leaderboard_for_lesson(
    lesson_id: UUID, uow: AbstractUnitOfWork
) -> Leaderboard:
    """Get leaderboard for a specific lesson."""
    with uow:
        lesson_repo: AbstractLessonRepository = uow.create_repository(
            AbstractLessonRepository
        )  # pyright: ignore
        submission_repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright: ignore

        lesson_entity = lesson_repo.get_lesson(lesson_id)
        if lesson_entity is None:
            return Leaderboard(entries=[])

        lesson = lesson_entity.as_model()
        exercise_ids = lesson.exercise_ids

        if not exercise_ids:
            return Leaderboard(entries=[])

        # Get max points for all users
        max_points = submission_repo.get_max_points_by_exercise_and_user(exercise_ids)

        if not max_points:
            return Leaderboard(entries=[])

        # Group by user
        user_points: dict[UUID, dict[UUID, int]] = {}
        for (exercise_id, user_id), points in max_points.items():
            if user_id not in user_points:
                user_points[user_id] = {}
            user_points[user_id][exercise_id] = points

        # Build progress entries
        entries: list[ProgressEntry] = []
        for user_id, exercise_points in user_points.items():
            user = _get_user_by_id(user_id, uow)
            if user is None:
                continue

            breakdown: dict[UUID, float] = {}
            total = 0.0
            for exercise_id in exercise_ids:
                points = exercise_points.get(exercise_id, 0)
                breakdown[exercise_id] = float(points)
                total += points

            scaled_total = total / len(exercise_ids) if exercise_ids else 0.0
            entries.append(ProgressEntry(user=user, total_points=scaled_total, breakdown=breakdown))

        # Sort by total_points descending
        entries.sort(key=lambda e: e.total_points, reverse=True)

        return Leaderboard(entries=entries)


def get_leaderboard_for_course(
    course_id: UUID, uow: AbstractUnitOfWork
) -> Leaderboard:
    """Get leaderboard for a specific course."""
    with uow:
        lesson_repo: AbstractLessonRepository = uow.create_repository(
            AbstractLessonRepository
        )  # pyright: ignore

        # Get all lessons in the course
        lesson_entities = lesson_repo.list_lessons_by_course(course_id)
        lessons = [e.as_model() for e in lesson_entities]

        if not lessons:
            return Leaderboard(entries=[])

        # Collect all exercise IDs from all lessons
        all_exercise_ids: list[UUID] = []
        lesson_exercises: dict[UUID, list[UUID]] = {}  # lesson_id -> exercise_ids
        for lesson in lessons:
            lesson_exercises[lesson.id] = lesson.exercise_ids
            all_exercise_ids.extend(lesson.exercise_ids)

        if not all_exercise_ids:
            return Leaderboard(entries=[])

        # Get all submissions for these exercises
        submission_repo: AbstractSubmissionRepository = uow.create_repository(
            AbstractSubmissionRepository
        )  # pyright: ignore
        max_points = submission_repo.get_max_points_by_exercise_and_user(all_exercise_ids)

        if not max_points:
            return Leaderboard(entries=[])

        # Group by user
        user_exercise_points: dict[UUID, dict[UUID, int]] = {}
        for (exercise_id, user_id), points in max_points.items():
            if user_id not in user_exercise_points:
                user_exercise_points[user_id] = {}
            user_exercise_points[user_id][exercise_id] = points

        # Build progress entries with per-lesson breakdown
        entries: list[ProgressEntry] = []
        for user_id, exercise_points in user_exercise_points.items():
            user = _get_user_by_id(user_id, uow)
            if user is None:
                continue

            breakdown: dict[UUID, float] = {}
            lesson_totals: list[float] = []

            for lesson in lessons:
                lesson_exercise_ids = lesson_exercises[lesson.id]
                if not lesson_exercise_ids:
                    continue

                lesson_total = 0.0
                for exercise_id in lesson_exercise_ids:
                    lesson_total += exercise_points.get(exercise_id, 0)

                lesson_avg = lesson_total / len(lesson_exercise_ids)
                breakdown[lesson.id] = lesson_avg
                lesson_totals.append(lesson_avg)

            # Course average is average of lesson averages
            course_avg = sum(lesson_totals) / len(lessons) if lessons else 0.0
            entries.append(ProgressEntry(user=user, total_points=course_avg, breakdown=breakdown))

        # Sort by total_points descending
        entries.sort(key=lambda e: e.total_points, reverse=True)

        return Leaderboard(entries=entries)