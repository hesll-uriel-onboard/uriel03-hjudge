"""Dashboard endpoint acceptance tests."""

import uuid

import pytest
import sqlalchemy as sa
from litestar.app import Litestar
from litestar.testing import TestClient

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.db.tables import course_table, lesson_table, course_admin_table, user_table
from hjudge.lms.services import course as course_services
from hjudge.lms.services import user as user_services
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


def create_exercise(uow: AbstractUnitOfWork, code: str) -> Exercise:
    """Create an exercise and return the model."""
    exercise_repo: AbstractExerciseRepository = uow.create_repository(
        AbstractExerciseRepository
    )  # pyright: ignore
    exercise = Exercise(judge=JudgeEnum.CODEFORCES, code=code)
    exercise_repo.add_exercise(ExerciseEntity.from_model(exercise))
    uow.commit()
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

def test_lesson_progress_requires_auth(app: Litestar, uow: AbstractUnitOfWork):
    """Test that lesson progress endpoint requires authentication."""
    admin = user_services.register("admin", "password", "Admin", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )
    lesson = course_services.create_lesson(
        course.id, "Lesson 1", "Content", "lesson-1", [], admin.id, uow
    )

    with TestClient(app) as client:
        response = client.get(f"/api/dashboard/lesson/{lesson.id}")
        assert response.status_code == 401


def test_lesson_progress_returns_200_for_authenticated_user(
    app: Litestar, uow: AbstractUnitOfWork
):
    """Test that lesson progress returns 200 for logged-in user."""
    user = user_services.register("student", "password", "Student", uow)
    admin = user_services.register("admin", "password", "Admin", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with uow:
        exercise = create_exercise(uow, "ex1")
        create_submission(uow, exercise, user.id, points=100)

    lesson = course_services.create_lesson(
        course.id, "Lesson 1", "Content", "lesson-1",
        [exercise.id], admin.id, uow
    )

    with TestClient(app) as client:
        # Login first
        login_resp = client.post(
            "/api/login",
            json={"username": "student", "password": "password"}
        )
        assert login_resp.status_code == 200
        cookie = login_resp.cookies.get("session")

        response = client.get(
            f"/api/dashboard/lesson/{lesson.id}",
            cookies={"session": cookie}
        )
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "total_points" in data
        assert "breakdown" in data


# ============ Lesson Leaderboard Tests ============

def test_lesson_leaderboard_is_public(app: Litestar, uow: AbstractUnitOfWork):
    """Test that lesson leaderboard is accessible without authentication."""
    admin = user_services.register("admin", "password", "Admin", uow)
    user = user_services.register("student", "password", "Student", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with uow:
        exercise = create_exercise(uow, "ex1")
        create_submission(uow, exercise, user.id, points=100)

    lesson = course_services.create_lesson(
        course.id, "Lesson 1", "Content", "lesson-1",
        [exercise.id], admin.id, uow
    )

    with TestClient(app) as client:
        # No authentication needed
        response = client.get(f"/api/dashboard/lesson/{lesson.id}/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert len(data["entries"]) == 1


def test_lesson_leaderboard_empty_when_no_submissions(
    app: Litestar, uow: AbstractUnitOfWork
):
    """Test that leaderboard is empty when there are no submissions."""
    admin = user_services.register("admin", "password", "Admin", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with uow:
        exercise = create_exercise(uow, "ex1")

    lesson = course_services.create_lesson(
        course.id, "Lesson 1", "Content", "lesson-1",
        [exercise.id], admin.id, uow
    )

    with TestClient(app) as client:
        response = client.get(f"/api/dashboard/lesson/{lesson.id}/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert data["entries"] == []


# ============ Course Progress Tests ============

def test_course_progress_requires_auth(app: Litestar, uow: AbstractUnitOfWork):
    """Test that course progress endpoint requires authentication."""
    admin = user_services.register("admin", "password", "Admin", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with TestClient(app) as client:
        response = client.get(f"/api/dashboard/course/{course.id}")
        assert response.status_code == 401


def test_course_progress_returns_200_for_authenticated_user(
    app: Litestar, uow: AbstractUnitOfWork
):
    """Test that course progress returns 200 for logged-in user."""
    user = user_services.register("student", "password", "Student", uow)
    admin = user_services.register("admin", "password", "Admin", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with uow:
        exercise = create_exercise(uow, "ex1")
        create_submission(uow, exercise, user.id, points=100)

    course_services.create_lesson(
        course.id, "Lesson 1", "Content", "lesson-1",
        [exercise.id], admin.id, uow
    )

    with TestClient(app) as client:
        login_resp = client.post(
            "/api/login",
            json={"username": "student", "password": "password"}
        )
        cookie = login_resp.cookies.get("session")

        response = client.get(
            f"/api/dashboard/course/{course.id}",
            cookies={"session": cookie}
        )
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "total_points" in data
        assert "breakdown" in data


# ============ Course Leaderboard Tests ============

def test_course_leaderboard_is_public(app: Litestar, uow: AbstractUnitOfWork):
    """Test that course leaderboard is accessible without authentication."""
    admin = user_services.register("admin", "password", "Admin", uow)
    user = user_services.register("student", "password", "Student", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    with uow:
        exercise = create_exercise(uow, "ex1")
        create_submission(uow, exercise, user.id, points=100)

    course_services.create_lesson(
        course.id, "Lesson 1", "Content", "lesson-1",
        [exercise.id], admin.id, uow
    )

    with TestClient(app) as client:
        response = client.get(f"/api/dashboard/course/{course.id}/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert len(data["entries"]) == 1