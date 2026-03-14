import pytest
from sqlalchemy import Engine

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.db.entities.course import (
    CourseEntity,
    LessonEntity,
)
from hjudge.lms.db.entities.user import UserEntity
from hjudge.lms.db.repositories.course import (
    AbstractCourseAdminRepository,
    AbstractCourseRepository,
    AbstractLessonRepository,
)
from hjudge.lms.db.repositories.user import AbstractUserRepository
from hjudge.lms.db.tables import (
    course_admin_table,
    course_table,
    lesson_table,
    user_table,
)
from hjudge.lms.models.course import Course, Lesson
from hjudge.lms.models.user import User


@pytest.fixture(autouse=True)
def clear_tables(engine: Engine):
    with engine.connect() as connection:
        connection.execute(course_admin_table.delete())
        connection.execute(lesson_table.delete())
        connection.execute(course_table.delete())
        connection.execute(user_table.delete())
        connection.commit()


def test_add_and_get_course(uow: AbstractUnitOfWork):
    with uow:
        course_repo: AbstractCourseRepository = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore
        course = Course(
            title="Test Course", content="Test Content", slug="test-course"
        )

        course_repo.add_course(CourseEntity.from_model(course))
        uow.commit()

        # Query by slug
        result = course_repo.get_course_by_slug("test-course")
        assert result is not None
        assert result.title == "Test Course"
        assert result.content == "Test Content"
        assert result.slug == "test-course"

        # Query by id
        result_by_id = course_repo.get_course(result.id)
        assert result_by_id is not None
        assert result_by_id.slug == "test-course"


def test_list_courses(uow: AbstractUnitOfWork):
    with uow:
        course_repo: AbstractCourseRepository = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore

        course1 = Course(title="Course 1", content="Content 1", slug="course-1")
        course2 = Course(title="Course 2", content="Content 2", slug="course-2")

        course_repo.add_course(CourseEntity.from_model(course1))
        course_repo.add_course(CourseEntity.from_model(course2))
        uow.commit()

    with uow:
        course_repo = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore
        results = course_repo.list_courses()
        assert len(results) == 2
        slugs = [r.slug for r in results]
        assert "course-1" in slugs
        assert "course-2" in slugs


def test_add_and_get_lesson(uow: AbstractUnitOfWork):
    with uow:
        course_repo: AbstractCourseRepository = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore
        lesson_repo: AbstractLessonRepository = uow.create_repository(
            AbstractLessonRepository
        )  # pyright: ignore

        course = Course(
            title="Test Course", content="Content", slug="test-course"
        )
        course_repo.add_course(CourseEntity.from_model(course))
        uow.commit()

        course_entity = course_repo.get_course_by_slug("test-course")
        assert course_entity is not None

        lesson = Lesson(
            title="Lesson 1",
            content="Lesson Content",
            slug="lesson-1",
            course=course,
            order=1,
            exercise_ids=[],
        )
        lesson_repo.add_lesson(LessonEntity.from_model(lesson))
        uow.commit()

        # Query by slug
        result = lesson_repo.get_lesson_by_slug("test-course", "lesson-1")
        assert result is not None
        assert result.title == "Lesson 1"
        assert result.order == 1


def test_list_lessons_by_course_ordered(uow: AbstractUnitOfWork):
    with uow:
        course_repo: AbstractCourseRepository = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore
        lesson_repo = uow.create_repository(
            AbstractLessonRepository
        )  # pyright: ignore

        course = Course(
            title="Test Course", content="Content", slug="test-course"
        )
        course_repo.add_course(CourseEntity.from_model(course))
        uow.commit()

        course_entity = course_repo.get_course_by_slug("test-course")
        assert course_entity is not None

        lesson1 = Lesson(
            title="Lesson 2",
            content="Content 2",
            slug="lesson-2",
            course=course,
            order=2,
            exercise_ids=[],
        )
        lesson2 = Lesson(
            title="Lesson 1",
            content="Content 1",
            slug="lesson-1",
            course=course,
            order=1,
            exercise_ids=[],
        )

        lesson_repo.add_lesson(LessonEntity.from_model(lesson1))
        lesson_repo.add_lesson(LessonEntity.from_model(lesson2))
        uow.commit()

    with uow:
        lesson_repo: AbstractLessonRepository = uow.create_repository(
            AbstractLessonRepository
        )  # pyright: ignore
        course_entity = course_repo.get_course_by_slug("test-course")
        assert course_entity is not None

        results = lesson_repo.list_lessons_by_course(course_entity.id)
        assert len(results) == 2
        # Should be ordered by order column
        assert results[0].order == 1
        assert results[1].order == 2


def test_add_and_check_admin(uow: AbstractUnitOfWork):
    with uow:
        user_repo: AbstractUserRepository = uow.create_repository(
            AbstractUserRepository
        )  # pyright: ignore
        course_repo: AbstractCourseRepository = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore
        admin_repo: AbstractCourseAdminRepository = uow.create_repository(
            AbstractCourseAdminRepository
        )  # pyright: ignore

        user = User(username="admin", password="test", name="Admin User")
        user_repo.add_user(UserEntity.from_model(user))
        uow.commit()

        user_entity = user_repo.get_user("admin")
        assert user_entity is not None

        course = Course(
            title="Test Course", content="Content", slug="test-course"
        )
        course_repo.add_course(CourseEntity.from_model(course))
        uow.commit()

        course_entity = course_repo.get_course_by_slug("test-course")
        assert course_entity is not None

        # Not admin yet
        assert admin_repo.is_admin(course_entity.id, user_entity.id) is False

        # Add admin
        admin_repo.add_admin(course_entity.id, user_entity.id)
        uow.commit()

        # Now admin
        assert admin_repo.is_admin(course_entity.id, user_entity.id) is True


def test_remove_admin(uow: AbstractUnitOfWork):
    with uow:
        user_repo: AbstractUserRepository = uow.create_repository(
            AbstractUserRepository
        )  # pyright: ignore
        course_repo: AbstractCourseRepository = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore
        admin_repo: AbstractCourseAdminRepository = uow.create_repository(
            AbstractCourseAdminRepository
        )  # pyright: ignore

        user = User(username="admin", password="test", name="Admin User")
        user_repo.add_user(UserEntity.from_model(user))
        uow.commit()

        user_entity = user_repo.get_user("admin")
        assert user_entity is not None

        course = Course(
            title="Test Course", content="Content", slug="test-course"
        )
        course_repo.add_course(CourseEntity.from_model(course))
        uow.commit()

        course_entity = course_repo.get_course_by_slug("test-course")
        assert course_entity is not None

        admin_repo.add_admin(course_entity.id, user_entity.id)
        uow.commit()

        assert admin_repo.is_admin(course_entity.id, user_entity.id) is True

        admin_repo.remove_admin(course_entity.id, user_entity.id)
        uow.commit()

        assert admin_repo.is_admin(course_entity.id, user_entity.id) is False


def test_list_admins(uow: AbstractUnitOfWork):
    with uow:
        user_repo: AbstractUserRepository = uow.create_repository(
            AbstractUserRepository
        )  # pyright: ignore
        course_repo: AbstractCourseRepository = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore
        admin_repo = uow.create_repository(
            AbstractCourseAdminRepository
        )  # pyright: ignore

        user1 = User(username="admin1", password="test", name="Admin 1")
        user2 = User(username="admin2", password="test", name="Admin 2")
        user_repo.add_user(UserEntity.from_model(user1))
        user_repo.add_user(UserEntity.from_model(user2))
        uow.commit()

        user1_entity = user_repo.get_user("admin1")
        user2_entity = user_repo.get_user("admin2")
        assert user1_entity is not None
        assert user2_entity is not None

        course = Course(
            title="Test Course", content="Content", slug="test-course"
        )
        course_repo.add_course(CourseEntity.from_model(course))
        uow.commit()

        course_entity = course_repo.get_course_by_slug("test-course")
        assert course_entity is not None
        course_id = course_entity.id

        admin_repo.add_admin(course_id, user1_entity.id)
        admin_repo.add_admin(course_id, user2_entity.id)
        uow.commit()

    with uow:
        admin_repo: AbstractCourseAdminRepository = uow.create_repository(
            AbstractCourseAdminRepository
        )  # pyright: ignore
        admins = admin_repo.list_admins(course_id)
        assert len(admins) == 2
        usernames = [a.username for a in admins]
        assert "admin1" in usernames
        assert "admin2" in usernames
