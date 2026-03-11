"""Test course API endpoints."""

import json

import pytest
from litestar import Litestar
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED
from litestar.testing import TestClient
from sqlalchemy import Engine

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.db.tables import course_admin_table, course_table, lesson_table, user_table
from hjudge.lms.services import course as course_services
from hjudge.lms.services import user as user_services


@pytest.fixture(autouse=True)
def clear_tables(engine: Engine):
    with engine.connect() as connection:
        connection.execute(course_admin_table.delete())
        connection.execute(lesson_table.delete())
        connection.execute(course_table.delete())
        connection.execute(user_table.delete())
        connection.commit()


def build_register_request(username: str, password: str, name: str) -> str:
    return json.dumps({"username": username, "password": password, "name": name})


def build_create_course_request(title: str, content: str, slug: str) -> str:
    return json.dumps({"title": title, "content": content, "slug": slug})


def build_update_course_request(title: str, content: str) -> str:
    return json.dumps({"title": title, "content": content})


def build_create_lesson_request(
    title: str, content: str, slug: str, exercise_ids: list = None
) -> str:
    return json.dumps(
        {"title": title, "content": content, "slug": slug, "exercise_ids": exercise_ids or []}
    )


def build_add_admin_request(user_id: str) -> str:
    return json.dumps({"user_id": user_id})


# ============ Course Tests ============


def test_create_course(app: Litestar, uow: AbstractUnitOfWork):
    # given: a registered user
    user = user_services.register("creator", "password", "Creator", uow)
    # and: logged in (get cookie)
    session = user_services.login("creator", "password", uow)
    cookie = session.cookie

    # when: creating a course
    with TestClient(app=app) as client:
        client.cookies.set("cookie", cookie)
        response = client.post(
            "/api/courses",
            content=build_create_course_request("Test Course", "Content", "test-course"),
        )

    # then: course is created
    assert response.status_code == HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Test Course"
    assert data["slug"] == "test-course"


def test_create_course_unauthenticated(app: Litestar):
    # when: creating a course without login
    with TestClient(app=app) as client:
        response = client.post(
            "/api/courses",
            content=build_create_course_request("Test Course", "Content", "test-course"),
        )

    # then: returns 401
    assert response.status_code == HTTP_401_UNAUTHORIZED


def test_list_courses(app: Litestar, uow: AbstractUnitOfWork):
    # given: some courses exist
    user = user_services.register("creator", "password", "Creator", uow)
    course_services.create_course("Course 1", "Content", "course-1", user.id, uow)
    course_services.create_course("Course 2", "Content", "course-2", user.id, uow)

    # when: listing courses
    with TestClient(app=app) as client:
        response = client.get("/api/courses")

    # then: all courses are returned
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert len(data["courses"]) == 2
    slugs = [c["slug"] for c in data["courses"]]
    assert "course-1" in slugs
    assert "course-2" in slugs


def test_get_course_by_slug(app: Litestar, uow: AbstractUnitOfWork):
    # given: a course exists
    user = user_services.register("creator", "password", "Creator", uow)
    course_services.create_course("Test Course", "Content", "test-course", user.id, uow)

    # when: getting course by slug
    with TestClient(app=app) as client:
        response = client.get("/api/courses/test-course")

    # then: course is returned
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["slug"] == "test-course"
    assert data["title"] == "Test Course"


def test_get_course_not_found(app: Litestar):
    # when: getting non-existent course
    with TestClient(app=app) as client:
        response = client.get("/api/courses/non-existent")

    # then: returns error
    assert response.status_code == 400


def test_update_course_by_admin(app: Litestar, uow: AbstractUnitOfWork):
    # given: a course with an admin
    user = user_services.register("creator", "password", "Creator", uow)
    course_services.create_course("Original", "Original", "test-course", user.id, uow)
    session = user_services.login("creator", "password", uow)
    cookie = session.cookie

    # when: admin updates course
    with TestClient(app=app) as client:
        client.cookies.set("cookie", cookie)
        response = client.patch(
            "/api/courses/test-course",
            content=build_update_course_request("Updated", "Updated"),
        )

    # then: course is updated
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated"


def test_update_course_by_non_admin(app: Litestar, uow: AbstractUnitOfWork):
    # given: a course created by user1
    user1 = user_services.register("creator", "password", "Creator", uow)
    user2 = user_services.register("other", "password", "Other", uow)
    course_services.create_course("Original", "Original", "test-course", user1.id, uow)
    session = user_services.login("other", "password", uow)
    cookie = session.cookie

    # when: non-admin tries to update
    with TestClient(app=app) as client:
        client.cookies.set("cookie", cookie)
        response = client.patch(
            "/api/courses/test-course",
            content=build_update_course_request("Updated", "Updated"),
        )

    # then: returns 401
    assert response.status_code == HTTP_401_UNAUTHORIZED


# ============ Lesson Tests ============


def test_create_lesson(app: Litestar, uow: AbstractUnitOfWork):
    # given: a course with an admin
    user = user_services.register("creator", "password", "Creator", uow)
    course_services.create_course("Test Course", "Content", "test-course", user.id, uow)
    session = user_services.login("creator", "password", uow)
    cookie = session.cookie

    # when: creating a lesson
    with TestClient(app=app) as client:
        client.cookies.set("cookie", cookie)
        response = client.post(
            "/api/courses/test-course/lessons",
            content=build_create_lesson_request("Lesson 1", "Content", "lesson-1"),
        )

    # then: lesson is created
    assert response.status_code == HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Lesson 1"
    assert data["order"] == 1


def test_list_lessons(app: Litestar, uow: AbstractUnitOfWork):
    # given: a course with lessons
    user = user_services.register("creator", "password", "Creator", uow)
    course = course_services.create_course("Test Course", "Content", "test-course", user.id, uow)
    course_services.create_lesson(course.id, "Lesson 1", "Content", "lesson-1", [], user.id, uow)
    course_services.create_lesson(course.id, "Lesson 2", "Content", "lesson-2", [], user.id, uow)

    # when: listing lessons
    with TestClient(app=app) as client:
        response = client.get("/api/courses/test-course/lessons")

    # then: lessons are returned in order
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert len(data["lessons"]) == 2
    assert data["lessons"][0]["order"] == 1
    assert data["lessons"][1]["order"] == 2


def test_get_lesson_by_slug(app: Litestar, uow: AbstractUnitOfWork):
    # given: a course with a lesson
    user = user_services.register("creator", "password", "Creator", uow)
    course = course_services.create_course("Test Course", "Content", "test-course", user.id, uow)
    course_services.create_lesson(course.id, "Lesson 1", "Content", "lesson-1", [], user.id, uow)

    # when: getting lesson by slug
    with TestClient(app=app) as client:
        response = client.get("/api/courses/test-course/lessons/lesson-1")

    # then: lesson is returned
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["slug"] == "lesson-1"


# ============ Admin Tests ============


def test_add_admin(app: Litestar, uow: AbstractUnitOfWork):
    # given: a course with one admin
    admin1 = user_services.register("admin1", "password", "Admin 1", uow)
    admin2 = user_services.register("admin2", "password", "Admin 2", uow)
    course_services.create_course("Test Course", "Content", "test-course", admin1.id, uow)
    session = user_services.login("admin1", "password", uow)
    cookie = session.cookie

    # when: adding another admin
    with TestClient(app=app) as client:
        client.cookies.set("cookie", cookie)
        response = client.post(
            f"/api/courses/test-course/admins",
            content=build_add_admin_request(str(admin2.id)),
        )

    # then: admin is added
    assert response.status_code == HTTP_200_OK
    assert course_services.is_admin(course_services.get_course_by_slug("test-course", uow).id, admin2.id, uow)


def test_remove_admin(app: Litestar, uow: AbstractUnitOfWork):
    # given: a course with two admins
    admin1 = user_services.register("admin1", "password", "Admin 1", uow)
    admin2 = user_services.register("admin2", "password", "Admin 2", uow)
    course = course_services.create_course("Test Course", "Content", "test-course", admin1.id, uow)
    course_services.add_course_admin(course.id, admin2.id, admin1.id, uow)
    session = user_services.login("admin1", "password", uow)
    cookie = session.cookie

    # when: removing admin
    with TestClient(app=app) as client:
        client.cookies.set("cookie", cookie)
        response = client.delete(f"/api/courses/test-course/admins/{admin2.id}")

    # then: admin is removed
    assert response.status_code == HTTP_200_OK
    assert not course_services.is_admin(course.id, admin2.id, uow)