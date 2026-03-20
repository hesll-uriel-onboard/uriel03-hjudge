"""Test dashboard services."""

import uuid

import pytest
import sqlalchemy as sa

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.db.tables import course_table, lesson_table, course_admin_table, user_table
from hjudge.lms.models.dashboard import ProgressEntry, Leaderboard
from hjudge.lms.models.course import Course, Lesson
from hjudge.lms.services import course as course_services
from hjudge.lms.services import user as user_services
from hjudge.lms.services import dashboard as dashboard_services
from hjudge.oj.db.entities.exercise import ExerciseEntity
from hjudge.oj.db.entities.submission import SubmissionEntity
from hjudge.oj.db.repositories.exercise import AbstractExerciseRepository
from hjudge.oj.db.repositories.submission import AbstractSubmissionRepository
from hjudge.oj.db.tables import exercise_table, submission_table
from hjudge.oj.models.judges import Exercise, JudgeEnum
from hjudge.oj.models.submission import Submission, Verdict


@pytest.fixture(autouse=True)
def clear_tables(engine: sa.Engine):
    with engine.connect() as connection:
        connection.execute(submission_table.delete())
        connection.execute(exercise_table.delete())
        connection.execute(lesson_table.delete())
        connection.execute(course_admin_table.delete())
        connection.execute(course_table.delete())
        connection.execute(user_table.delete())
        connection.commit()


# ============ Helper Functions ============

def create_exercise(uow: AbstractUnitOfWork, code: str) -> Exercise:
    """Create an exercise and return the model."""
    exercise_repo: AbstractExerciseRepository = uow.create_repository(
        AbstractExerciseRepository
    )  # pyright: ignore
    exercise = Exercise(judge=JudgeEnum.CODEFORCES, code=code)
    exercise_repo.add_exercise(ExerciseEntity.from_model(exercise))
    uow.commit()
    # Fetch to get ID
    entity = exercise_repo.get_exercise_by_judge_and_code(JudgeEnum.CODEFORCES, code)
    assert entity is not None
    return entity.as_model()


def create_submission(
    uow: AbstractUnitOfWork,
    exercise: Exercise,
    user_id: uuid.UUID,
    points: int,
    verdict: Verdict = Verdict.AC,
) -> Submission:
    """Create a submission and return the model."""
    submission_repo: AbstractSubmissionRepository = uow.create_repository(
        AbstractSubmissionRepository
    )  # pyright: ignore
    submission = Submission(
        exercise=exercise,
        user_id=user_id,
        verdict=verdict,
        submission_id=f"sub_{uuid.uuid4().hex[:8]}",
        points=points,
    )
    submission_repo.add_submission(SubmissionEntity.from_model(submission))
    uow.commit()
    return submission


# ============ Lesson Progress Tests ============

def test_get_progress_for_lesson_single_user(uow: AbstractUnitOfWork):
    """Test progress calculation for a single user in a lesson."""
    # given: a user and a course with a lesson containing 3 exercises
    user = user_services.register("student", "password", "Student", uow)
    admin = user_services.register("admin", "password", "Admin", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with uow:
        exercise1 = create_exercise(uow, "ex1")
        exercise2 = create_exercise(uow, "ex2")
        exercise3 = create_exercise(uow, "ex3")

        # Create submissions with varying points
        create_submission(uow, exercise1, user.id, points=100)  # 100%
        create_submission(uow, exercise2, user.id, points=50)   # 50%
        create_submission(uow, exercise3, user.id, points=0)    # 0%

    lesson = course_services.create_lesson(
        course_id=course.id,
        title="Lesson 1",
        content="Content",
        slug="lesson-1",
        exercise_ids=[exercise1.id, exercise2.id, exercise3.id],
        user_id=admin.id,
        uow=uow,
    )

    # when: getting user's progress
    progress = dashboard_services.get_progress_for_lesson(user.id, lesson.id, uow)

    # then: total points should be (100 + 50 + 0) / 3 = 50
    assert progress is not None
    assert progress.user.id == user.id
    assert progress.total_points == pytest.approx(50.0)
    assert progress.breakdown[exercise1.id] == 100.0
    assert progress.breakdown[exercise2.id] == 50.0
    assert progress.breakdown[exercise3.id] == 0.0


def test_get_progress_for_lesson_max_points(uow: AbstractUnitOfWork):
    """Test that progress uses max points across multiple submissions."""
    # given: a user with multiple submissions for same exercise
    user = user_services.register("student", "password", "Student", uow)
    admin = user_services.register("admin", "password", "Admin", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with uow:
        exercise = create_exercise(uow, "ex1")

        # Multiple submissions with different points
        create_submission(uow, exercise, user.id, points=30, verdict=Verdict.WA)
        create_submission(uow, exercise, user.id, points=50, verdict=Verdict.WA)
        create_submission(uow, exercise, user.id, points=80, verdict=Verdict.AC)  # max

    lesson = course_services.create_lesson(
        course_id=course.id,
        title="Lesson 1",
        content="Content",
        slug="lesson-1",
        exercise_ids=[exercise.id],
        user_id=admin.id,
        uow=uow,
    )

    # when: getting user's progress
    progress = dashboard_services.get_progress_for_lesson(user.id, lesson.id, uow)

    # then: should use max points (80)
    assert progress.total_points == 80.0
    assert progress.breakdown[exercise.id] == 80.0


def test_get_progress_for_lesson_no_submissions(uow: AbstractUnitOfWork):
    """Test progress when user has no submissions."""
    # given: a lesson with exercises but no submissions
    user = user_services.register("student", "password", "Student", uow)
    admin = user_services.register("admin", "password", "Admin", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with uow:
        exercise1 = create_exercise(uow, "ex1")
        exercise2 = create_exercise(uow, "ex2")

    lesson = course_services.create_lesson(
        course_id=course.id,
        title="Lesson 1",
        content="Content",
        slug="lesson-1",
        exercise_ids=[exercise1.id, exercise2.id],
        user_id=admin.id,
        uow=uow,
    )

    # when: getting user's progress
    progress = dashboard_services.get_progress_for_lesson(user.id, lesson.id, uow)

    # then: progress should be 0
    assert progress.total_points == 0.0
    assert len(progress.breakdown) == 2
    assert progress.breakdown[exercise1.id] == 0.0
    assert progress.breakdown[exercise2.id] == 0.0


def test_get_progress_for_lesson_empty_exercises(uow: AbstractUnitOfWork):
    """Test progress for lesson with no exercises."""
    # given: a lesson with no exercises
    user = user_services.register("student", "password", "Student", uow)
    admin = user_services.register("admin", "password", "Admin", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    lesson = course_services.create_lesson(
        course_id=course.id,
        title="Lesson 1",
        content="Content",
        slug="lesson-1",
        exercise_ids=[],
        user_id=admin.id,
        uow=uow,
    )

    # when: getting user's progress
    progress = dashboard_services.get_progress_for_lesson(user.id, lesson.id, uow)

    # then: progress should be 0 with empty breakdown
    assert progress.total_points == 0.0
    assert len(progress.breakdown) == 0


# ============ Course Progress Tests ============

def test_get_progress_for_course(uow: AbstractUnitOfWork):
    """Test progress calculation for a course with multiple lessons."""
    # given: a course with 2 lessons
    user = user_services.register("student", "password", "Student", uow)
    admin = user_services.register("admin", "password", "Admin", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with uow:
        exercise1 = create_exercise(uow, "ex1")
        exercise2 = create_exercise(uow, "ex2")

        # User gets 100% on lesson 1 (1 exercise, 100 points)
        create_submission(uow, exercise1, user.id, points=100)

        # User gets 50% on lesson 2 (1 exercise, 50 points)
        create_submission(uow, exercise2, user.id, points=50)

    lesson1 = course_services.create_lesson(
        course_id=course.id,
        title="Lesson 1",
        content="Content",
        slug="lesson-1",
        exercise_ids=[exercise1.id],
        user_id=admin.id,
        uow=uow,
    )

    lesson2 = course_services.create_lesson(
        course_id=course.id,
        title="Lesson 2",
        content="Content",
        slug="lesson-2",
        exercise_ids=[exercise2.id],
        user_id=admin.id,
        uow=uow,
    )

    # when: getting user's course progress
    progress = dashboard_services.get_progress_for_course(user.id, course.id, uow)

    # then: total should be (100 + 50) / 2 = 75
    assert progress.total_points == pytest.approx(75.0)
    assert progress.breakdown[lesson1.id] == 100.0
    assert progress.breakdown[lesson2.id] == 50.0


def test_get_progress_for_course_no_lessons(uow: AbstractUnitOfWork):
    """Test progress for course with no lessons."""
    # given: a course with no lessons
    user = user_services.register("student", "password", "Student", uow)
    admin = user_services.register("admin", "password", "Admin", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    # when: getting user's course progress
    progress = dashboard_services.get_progress_for_course(user.id, course.id, uow)

    # then: progress should be 0
    assert progress.total_points == 0.0
    assert len(progress.breakdown) == 0


# ============ Leaderboard Tests ============

def test_get_leaderboard_for_lesson(uow: AbstractUnitOfWork):
    """Test leaderboard for a lesson with multiple users."""
    # given: a lesson with 2 exercises and 3 users
    admin = user_services.register("admin", "password", "Admin", uow)
    user1 = user_services.register("user1", "password", "User 1", uow)
    user2 = user_services.register("user2", "password", "User 2", uow)
    user3 = user_services.register("user3", "password", "User 3", uow)

    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with uow:
        exercise1 = create_exercise(uow, "ex1")
        exercise2 = create_exercise(uow, "ex2")

        # User 1: 100 + 90 = 190/2 = 95%
        create_submission(uow, exercise1, user1.id, points=100)
        create_submission(uow, exercise2, user1.id, points=90)

        # User 2: 100 + 100 = 200/2 = 100%
        create_submission(uow, exercise1, user2.id, points=100)
        create_submission(uow, exercise2, user2.id, points=100)

        # User 3: 50 + 0 = 50/2 = 25%
        create_submission(uow, exercise1, user3.id, points=50)
        create_submission(uow, exercise2, user3.id, points=0)

    lesson = course_services.create_lesson(
        course_id=course.id,
        title="Lesson 1",
        content="Content",
        slug="lesson-1",
        exercise_ids=[exercise1.id, exercise2.id],
        user_id=admin.id,
        uow=uow,
    )

    # when: getting leaderboard
    leaderboard = dashboard_services.get_leaderboard_for_lesson(lesson.id, uow)

    # then: should be sorted by total_points descending
    assert len(leaderboard.entries) == 3
    assert leaderboard.entries[0].user.id == user2.id
    assert leaderboard.entries[0].total_points == 100.0

    assert leaderboard.entries[1].user.id == user1.id
    assert leaderboard.entries[1].total_points == 95.0

    assert leaderboard.entries[2].user.id == user3.id
    assert leaderboard.entries[2].total_points == 25.0


def test_get_leaderboard_for_course(uow: AbstractUnitOfWork):
    """Test leaderboard for a course with multiple lessons."""
    # given: a course with 2 lessons and 2 users
    admin = user_services.register("admin", "password", "Admin", uow)
    user1 = user_services.register("user1", "password", "User 1", uow)
    user2 = user_services.register("user2", "password", "User 2", uow)

    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with uow:
        exercise1 = create_exercise(uow, "ex1")
        exercise2 = create_exercise(uow, "ex2")

        # User 1: lesson1=100%, lesson2=50%
        create_submission(uow, exercise1, user1.id, points=100)
        create_submission(uow, exercise2, user1.id, points=50)

        # User 2: lesson1=80%, lesson2=100%
        create_submission(uow, exercise1, user2.id, points=80)
        create_submission(uow, exercise2, user2.id, points=100)

    lesson1 = course_services.create_lesson(
        course_id=course.id,
        title="Lesson 1",
        content="Content",
        slug="lesson-1",
        exercise_ids=[exercise1.id],
        user_id=admin.id,
        uow=uow,
    )

    lesson2 = course_services.create_lesson(
        course_id=course.id,
        title="Lesson 2",
        content="Content",
        slug="lesson-2",
        exercise_ids=[exercise2.id],
        user_id=admin.id,
        uow=uow,
    )

    # when: getting leaderboard
    leaderboard = dashboard_services.get_leaderboard_for_course(course.id, uow)

    # then: sorted by total, breakdown shows per-lesson scores
    assert len(leaderboard.entries) == 2

    # User 1: (100 + 50) / 2 = 75%
    # User 2: (80 + 100) / 2 = 90%
    assert leaderboard.entries[0].user.id == user2.id
    assert leaderboard.entries[0].total_points == 90.0
    assert leaderboard.entries[0].breakdown[lesson1.id] == 80.0
    assert leaderboard.entries[0].breakdown[lesson2.id] == 100.0

    assert leaderboard.entries[1].user.id == user1.id
    assert leaderboard.entries[1].total_points == 75.0


def test_get_leaderboard_for_lesson_no_submissions(uow: AbstractUnitOfWork):
    """Test leaderboard when no submissions exist."""
    # given: a lesson with exercises but no submissions
    admin = user_services.register("admin", "password", "Admin", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with uow:
        exercise = create_exercise(uow, "ex1")

    lesson = course_services.create_lesson(
        course_id=course.id,
        title="Lesson 1",
        content="Content",
        slug="lesson-1",
        exercise_ids=[exercise.id],
        user_id=admin.id,
        uow=uow,
    )

    # when: getting leaderboard
    leaderboard = dashboard_services.get_leaderboard_for_lesson(lesson.id, uow)

    # then: should be empty
    assert len(leaderboard.entries) == 0


def test_leaderboard_excludes_users_without_submissions(uow: AbstractUnitOfWork):
    """Test that users without submissions don't appear in leaderboard."""
    # given: a lesson with some submissions and users without submissions
    admin = user_services.register("admin", "password", "Admin", uow)
    user_with_sub = user_services.register("active", "password", "Active", uow)
    user_without_sub = user_services.register("inactive", "password", "Inactive", uow)

    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with uow:
        exercise = create_exercise(uow, "ex1")
        create_submission(uow, exercise, user_with_sub.id, points=100)

    lesson = course_services.create_lesson(
        course_id=course.id,
        title="Lesson 1",
        content="Content",
        slug="lesson-1",
        exercise_ids=[exercise.id],
        user_id=admin.id,
        uow=uow,
    )

    # when: getting leaderboard
    leaderboard = dashboard_services.get_leaderboard_for_lesson(lesson.id, uow)

    # then: only user with submissions appears
    assert len(leaderboard.entries) == 1
    assert leaderboard.entries[0].user.id == user_with_sub.id