"""Test course services."""

import pytest
import sqlalchemy as sa

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.db.tables import course_table, lesson_table, course_admin_table, user_table
from hjudge.lms.errors import (
    CourseNotFoundError,
    CourseSlugExistsError,
    LessonSlugExistsError,
    NotCourseAdminError,
    CannotRemoveLastAdminError,
)
from hjudge.lms.models.course import Course, Lesson
from hjudge.lms.models.user import User
from hjudge.lms.services import course as course_services
from hjudge.lms.services import user as user_services


@pytest.fixture(autouse=True)
def clear_tables(engine: sa.Engine):
    with engine.connect() as connection:
        connection.execute(course_admin_table.delete())
        connection.execute(lesson_table.delete())
        connection.execute(course_table.delete())
        connection.execute(user_table.delete())
        connection.commit()


# ============ Course Creation Tests ============

def test_create_course_success(uow: AbstractUnitOfWork):
    # given: a registered user
    user = user_services.register("creator", "password", "Creator", uow)

    # when: user creates a course
    course = course_services.create_course(
        title="Test Course",
        content="Test Content",
        slug="test-course",
        creator_user_id=user.id,
        uow=uow,
    )

    # then: course is created
    assert course.title == "Test Course"
    assert course.slug == "test-course"

    # and: creator is admin
    assert course_services.is_admin(course.id, user.id, uow) is True


def test_create_course_duplicate_slug(uow: AbstractUnitOfWork):
    # given: a user and a course with slug "test-course"
    user = user_services.register("creator", "password", "Creator", uow)
    course_services.create_course(
        title="First Course",
        content="Content",
        slug="test-course",
        creator_user_id=user.id,
        uow=uow,
    )

    # when: trying to create another course with same slug
    with pytest.raises(CourseSlugExistsError):
        course_services.create_course(
            title="Second Course",
            content="Content",
            slug="test-course",
            creator_user_id=user.id,
            uow=uow,
        )


# ============ Course Update Tests ============

def test_update_course_by_admin(uow: AbstractUnitOfWork):
    # given: a course with an admin
    user = user_services.register("creator", "password", "Creator", uow)
    course = course_services.create_course(
        title="Original Title",
        content="Original Content",
        slug="test-course",
        creator_user_id=user.id,
        uow=uow,
    )

    # when: admin updates the course
    updated = course_services.update_course(
        course_id=course.id,
        title="New Title",
        content="New Content",
        user_id=user.id,
        uow=uow,
    )

    # then: course is updated
    assert updated.title == "New Title"
    assert updated.content == "New Content"


def test_update_course_by_non_admin(uow: AbstractUnitOfWork):
    # given: a course created by user1
    user1 = user_services.register("creator", "password", "Creator", uow)
    user2 = user_services.register("other", "password", "Other", uow)
    course = course_services.create_course(
        title="Original Title",
        content="Original Content",
        slug="test-course",
        creator_user_id=user1.id,
        uow=uow,
    )

    # when: non-admin tries to update
    with pytest.raises(NotCourseAdminError):
        course_services.update_course(
            course_id=course.id,
            title="New Title",
            content="New Content",
            user_id=user2.id,
            uow=uow,
        )


# ============ Lesson Creation Tests ============

def test_create_lesson_success(uow: AbstractUnitOfWork):
    # given: a course with an admin
    user = user_services.register("creator", "password", "Creator", uow)
    course = course_services.create_course(
        title="Test Course",
        content="Content",
        slug="test-course",
        creator_user_id=user.id,
        uow=uow,
    )

    # when: admin creates a lesson
    lesson = course_services.create_lesson(
        course_id=course.id,
        title="Lesson 1",
        content="Lesson Content",
        slug="lesson-1",
        exercise_ids=[],
        user_id=user.id,
        uow=uow,
    )

    # then: lesson is created with order 1
    assert lesson.title == "Lesson 1"
    assert lesson.order == 1


def test_create_lesson_auto_order(uow: AbstractUnitOfWork):
    # given: a course with one lesson
    user = user_services.register("creator", "password", "Creator", uow)
    course = course_services.create_course(
        title="Test Course",
        content="Content",
        slug="test-course",
        creator_user_id=user.id,
        uow=uow,
    )
    course_services.create_lesson(
        course_id=course.id,
        title="Lesson 1",
        content="Content",
        slug="lesson-1",
        exercise_ids=[],
        user_id=user.id,
        uow=uow,
    )

    # when: creating another lesson
    lesson2 = course_services.create_lesson(
        course_id=course.id,
        title="Lesson 2",
        content="Content",
        slug="lesson-2",
        exercise_ids=[],
        user_id=user.id,
        uow=uow,
    )

    # then: order is 2
    assert lesson2.order == 2


def test_create_lesson_by_non_admin(uow: AbstractUnitOfWork):
    # given: a course created by user1
    user1 = user_services.register("creator", "password", "Creator", uow)
    user2 = user_services.register("other", "password", "Other", uow)
    course = course_services.create_course(
        title="Test Course",
        content="Content",
        slug="test-course",
        creator_user_id=user1.id,
        uow=uow,
    )

    # when: non-admin tries to create lesson
    with pytest.raises(NotCourseAdminError):
        course_services.create_lesson(
            course_id=course.id,
            title="Lesson 1",
            content="Content",
            slug="lesson-1",
            exercise_ids=[],
            user_id=user2.id,
            uow=uow,
        )


def test_create_lesson_duplicate_slug_same_course(uow: AbstractUnitOfWork):
    # given: a course with a lesson
    user = user_services.register("creator", "password", "Creator", uow)
    course = course_services.create_course(
        title="Test Course",
        content="Content",
        slug="test-course",
        creator_user_id=user.id,
        uow=uow,
    )
    course_services.create_lesson(
        course_id=course.id,
        title="Lesson 1",
        content="Content",
        slug="lesson-1",
        exercise_ids=[],
        user_id=user.id,
        uow=uow,
    )

    # when: creating another lesson with same slug
    with pytest.raises(LessonSlugExistsError):
        course_services.create_lesson(
            course_id=course.id,
            title="Lesson 1 Duplicate",
            content="Content",
            slug="lesson-1",
            exercise_ids=[],
            user_id=user.id,
            uow=uow,
        )


def test_create_lesson_same_slug_different_course(uow: AbstractUnitOfWork):
    # given: two courses
    user = user_services.register("creator", "password", "Creator", uow)
    course1 = course_services.create_course(
        title="Course 1",
        content="Content",
        slug="course-1",
        creator_user_id=user.id,
        uow=uow,
    )
    course2 = course_services.create_course(
        title="Course 2",
        content="Content",
        slug="course-2",
        creator_user_id=user.id,
        uow=uow,
    )
    course_services.create_lesson(
        course_id=course1.id,
        title="Lesson",
        content="Content",
        slug="lesson-1",
        exercise_ids=[],
        user_id=user.id,
        uow=uow,
    )

    # when: creating lesson with same slug in different course
    lesson = course_services.create_lesson(
        course_id=course2.id,
        title="Lesson",
        content="Content",
        slug="lesson-1",
        exercise_ids=[],
        user_id=user.id,
        uow=uow,
    )

    # then: it succeeds
    assert lesson.slug == "lesson-1"


# ============ Listing Tests ============

def test_list_courses(uow: AbstractUnitOfWork):
    # given: multiple courses
    user = user_services.register("creator", "password", "Creator", uow)
    course_services.create_course("Course 1", "Content", "course-1", user.id, uow)
    course_services.create_course("Course 2", "Content", "course-2", user.id, uow)

    # when: listing courses
    courses = course_services.list_courses(uow)

    # then: all courses are returned
    assert len(courses) == 2
    slugs = [c.slug for c in courses]
    assert "course-1" in slugs
    assert "course-2" in slugs


def test_list_lessons_ordered(uow: AbstractUnitOfWork):
    # given: a course with lessons added in random order
    user = user_services.register("creator", "password", "Creator", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", user.id, uow
    )
    course_services.create_lesson(
        course.id, "Lesson 2", "Content", "lesson-2", [], user.id, uow
    )
    course_services.create_lesson(
        course.id, "Lesson 1", "Content", "lesson-1", [], user.id, uow
    )
    course_services.create_lesson(
        course.id, "Lesson 3", "Content", "lesson-3", [], user.id, uow
    )

    # when: listing lessons
    lessons = course_services.list_lessons(course.id, uow)

    # then: lessons are ordered by order field
    assert len(lessons) == 3
    assert lessons[0].order == 1
    assert lessons[1].order == 2
    assert lessons[2].order == 3


# ============ Admin Management Tests ============

def test_add_admin_by_admin(uow: AbstractUnitOfWork):
    # given: a course with one admin
    admin1 = user_services.register("admin1", "password", "Admin 1", uow)
    admin2 = user_services.register("admin2", "password", "Admin 2", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin1.id, uow
    )

    # when: admin adds another admin
    course_services.add_course_admin(course.id, admin2.id, admin1.id, uow)

    # then: new admin is added
    assert course_services.is_admin(course.id, admin2.id, uow) is True


def test_add_admin_by_non_admin(uow: AbstractUnitOfWork):
    # given: a course and two non-admins
    admin = user_services.register("admin", "password", "Admin", uow)
    user1 = user_services.register("user1", "password", "User 1", uow)
    user2 = user_services.register("user2", "password", "User 2", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    # when: non-admin tries to add admin
    with pytest.raises(NotCourseAdminError):
        course_services.add_course_admin(course.id, user2.id, user1.id, uow)


def test_remove_admin_by_admin(uow: AbstractUnitOfWork):
    # given: a course with two admins
    admin1 = user_services.register("admin1", "password", "Admin 1", uow)
    admin2 = user_services.register("admin2", "password", "Admin 2", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin1.id, uow
    )
    course_services.add_course_admin(course.id, admin2.id, admin1.id, uow)

    # when: removing one admin
    course_services.remove_course_admin(course.id, admin2.id, admin1.id, uow)

    # then: admin is removed
    assert course_services.is_admin(course.id, admin2.id, uow) is False


def test_remove_last_admin(uow: AbstractUnitOfWork):
    # given: a course with only one admin
    admin = user_services.register("admin", "password", "Admin", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", admin.id, uow
    )

    # when: trying to remove the last admin
    with pytest.raises(CannotRemoveLastAdminError):
        course_services.remove_course_admin(course.id, admin.id, admin.id, uow)


# ============ Get Course/Lesson Tests ============

def test_get_course_by_slug(uow: AbstractUnitOfWork):
    # given: a course
    user = user_services.register("creator", "password", "Creator", uow)
    course_services.create_course(
        "Test Course", "Content", "test-course", user.id, uow
    )

    # when: getting course by slug
    course = course_services.get_course_by_slug("test-course", uow)

    # then: course is returned
    assert course is not None
    assert course.slug == "test-course"


def test_get_course_by_slug_not_found(uow: AbstractUnitOfWork):
    # when: getting non-existent course
    course = course_services.get_course_by_slug("non-existent", uow)

    # then: None is returned
    assert course is None


def test_get_lesson_by_slug(uow: AbstractUnitOfWork):
    # given: a course with a lesson
    user = user_services.register("creator", "password", "Creator", uow)
    course = course_services.create_course(
        "Test Course", "Content", "test-course", user.id, uow
    )
    course_services.create_lesson(
        course.id, "Lesson 1", "Content", "lesson-1", [], user.id, uow
    )

    # when: getting lesson by slug
    lesson = course_services.get_lesson_by_slug("test-course", "lesson-1", uow)

    # then: lesson is returned
    assert lesson is not None
    assert lesson.slug == "lesson-1"


def test_get_lesson_by_slug_not_found(uow: AbstractUnitOfWork):
    # when: getting non-existent lesson
    lesson = course_services.get_lesson_by_slug("non-existent", "lesson-1", uow)

    # then: None is returned
    assert lesson is None


# ============ Lesson Update Tests ============


def test_update_lesson_by_admin(uow: AbstractUnitOfWork):
    # given: a course with a lesson
    user = user_services.register("creator", "password", "Creator", uow)
    course = course_services.create_course(
        title="Test Course",
        content="Content",
        slug="test-course",
        creator_user_id=user.id,
        uow=uow,
    )
    lesson = course_services.create_lesson(
        course_id=course.id,
        title="Original Title",
        content="Original Content",
        slug="lesson-1",
        exercise_ids=[],
        user_id=user.id,
        uow=uow,
    )

    # when: admin updates the lesson
    updated = course_services.update_lesson(
        lesson_id=lesson.id,
        title="New Title",
        content="New Content",
        exercise_ids=[],
        user_id=user.id,
        uow=uow,
    )

    # then: lesson is updated
    assert updated.title == "New Title"
    assert updated.content == "New Content"


def test_update_lesson_by_non_admin(uow: AbstractUnitOfWork):
    # given: a course with a lesson created by user1
    user1 = user_services.register("creator", "password", "Creator", uow)
    user2 = user_services.register("other", "password", "Other", uow)
    course = course_services.create_course(
        title="Test Course",
        content="Content",
        slug="test-course",
        creator_user_id=user1.id,
        uow=uow,
    )
    lesson = course_services.create_lesson(
        course_id=course.id,
        title="Original Title",
        content="Original Content",
        slug="lesson-1",
        exercise_ids=[],
        user_id=user1.id,
        uow=uow,
    )

    # when: non-admin tries to update
    with pytest.raises(NotCourseAdminError):
        course_services.update_lesson(
            lesson_id=lesson.id,
            title="New Title",
            content="New Content",
            exercise_ids=[],
            user_id=user2.id,
            uow=uow,
        )