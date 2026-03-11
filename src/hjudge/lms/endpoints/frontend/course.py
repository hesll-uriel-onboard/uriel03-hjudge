from typing import Any

from litestar import MediaType, get
from litestar.datastructures import State
from litestar.response import Template

from hjudge.commons.db.uow import AbstractUOWFactory
from hjudge.lms.endpoints.authentication import authenticate_user
from hjudge.lms.endpoints.responses.user import COOKIE_KEY
from hjudge.lms.errors import NotCourseAdminError
from hjudge.lms.services import course as course_services
# from hjudge.oj.db.repositories.exercise import AbstractExerciseRepository


@get("/courses", media_type=MediaType.HTML, include_in_schema=False)
async def courses_page(
    cookies: dict[str, str],
    uow_factory: AbstractUOWFactory,
) -> Template:
    cookie: str | None = cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=False)

    courses = course_services.list_courses(uow_factory.create_uow())

    return Template(
        template_name="views/course/index.jinja",
        context={"user": user, "courses": courses},
    )


@get("/courses/new", media_type=MediaType.HTML, include_in_schema=False)
async def new_course_page(
    cookies: dict[str, str],
    uow_factory: AbstractUOWFactory,
) -> Template:
    cookie: str | None = cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=True)

    return Template(
        template_name="views/course/new.jinja",
        context={"user": user},
    )


@get("/courses/{slug:str}/edit", media_type=MediaType.HTML, include_in_schema=False)
async def edit_course_page(
    slug: str,
    cookies: dict[str, str],
    uow_factory: AbstractUOWFactory,
) -> Template:
    cookie: str | None = cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=True)

    course = course_services.get_course_by_slug(slug, uow_factory.create_uow())
    if course is None:
        # TODO: proper 404 handling
        return Template(
            template_name="views/course/index.jinja",
            context={"user": user, "courses": []},
        )

    # Check if user is admin
    if not course_services.is_admin(course.id, user.id, uow_factory.create_uow()):
        raise NotCourseAdminError()

    return Template(
        template_name="views/course/edit.jinja",
        context={"user": user, "course": course},
    )


@get("/courses/{slug:str}", media_type=MediaType.HTML, include_in_schema=False)
async def course_detail_page(
    slug: str,
    cookies: dict[str, str],
    uow_factory: AbstractUOWFactory,
) -> Template:
    cookie: str | None = cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=False)

    course = course_services.get_course_by_slug(slug, uow_factory.create_uow())
    if course is None:
        # TODO: proper 404 handling
        return Template(
            template_name="views/course/index.jinja",
            context={"user": user, "courses": []},
        )

    lessons = course_services.list_lessons(course.id, uow_factory.create_uow())

    is_admin = False
    if user is not None:
        is_admin = course_services.is_admin(course.id, user.id, uow_factory.create_uow())

    return Template(
        template_name="views/course/detail.jinja",
        context={"user": user, "course": course, "lessons": lessons, "is_admin": is_admin},
    )


@get("/courses/{slug:str}/lessons/new", media_type=MediaType.HTML, include_in_schema=False)
async def new_lesson_page(
    slug: str,
    cookies: dict[str, str],
    uow_factory: AbstractUOWFactory,
) -> Template:
    cookie: str | None = cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=True)

    course = course_services.get_course_by_slug(slug, uow_factory.create_uow())
    if course is None:
        # TODO: proper 404 handling
        return Template(
            template_name="views/course/index.jinja",
            context={"user": user, "courses": []},
        )

    # Check if user is admin
    if not course_services.is_admin(course.id, user.id, uow_factory.create_uow()):
        raise NotCourseAdminError()

    return Template(
        template_name="views/course/lesson/new.jinja",
        context={"user": user, "course": course},
    )


@get("/courses/{course_slug:str}/lessons/{lesson_slug:str}/edit", media_type=MediaType.HTML, include_in_schema=False)
async def edit_lesson_page(
    course_slug: str,
    lesson_slug: str,
    cookies: dict[str, str],
    uow_factory: AbstractUOWFactory,
) -> Template:
    cookie: str | None = cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=True)

    lesson = course_services.get_lesson_by_slug(course_slug, lesson_slug, uow_factory.create_uow())
    if lesson is None:
        # TODO: proper 404 handling
        return Template(
            template_name="views/course/index.jinja",
            context={"user": user, "courses": []},
        )

    course = lesson.course

    # Check if user is admin
    if not course_services.is_admin(course.id, user.id, uow_factory.create_uow()):
        raise NotCourseAdminError()

    return Template(
        template_name="views/course/lesson/edit.jinja",
        context={"user": user, "course": course, "lesson": lesson},
    )


@get("/courses/{course_slug:str}/lessons/{lesson_slug:str}", media_type=MediaType.HTML, include_in_schema=False)
async def lesson_detail_page(
    course_slug: str,
    lesson_slug: str,
    cookies: dict[str, str],
    uow_factory: AbstractUOWFactory,
) -> Template:
    cookie: str | None = cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=False)

    lesson = course_services.get_lesson_by_slug(course_slug, lesson_slug, uow_factory.create_uow())
    if lesson is None:
        # TODO: proper 404 handling
        return Template(
            template_name="views/course/index.jinja",
            context={"user": user, "courses": []},
        )

    course = lesson.course
    lessons = course_services.list_lessons(course.id, uow_factory.create_uow())

    is_admin = False
    if user is not None:
        is_admin = course_services.is_admin(course.id, user.id, uow_factory.create_uow())

    # Find previous and next lessons
    prev_lesson = None
    next_lesson = None
    for i, l in enumerate(lessons):
        if l.id == lesson.id:
            if i > 0:
                prev_lesson = lessons[i - 1]
            if i < len(lessons) - 1:
                next_lesson = lessons[i + 1]
            break

    # # Fetch exercises for this lesson
    # exercises = []
    # if lesson.exercise_ids:
    #     with uow_factory.create_uow() as uow:
    #         exercise_repo: AbstractExerciseRepository = uow.create_repository(
    #             AbstractExerciseRepository
    #         )  # pyright: ignore
    #         for exercise_id in lesson.exercise_ids:
    #             exercise_entity = exercise_repo.get_exercise(exercise_id)
    #             if exercise_entity:
    #                 exercises.append(exercise_entity.as_model())
    #         uow.rollback()

    return Template(
        template_name="views/course/lesson/detail.jinja",
        context={
            "user": user,
            "course": course,
            "lesson": lesson,
            "prev_lesson": prev_lesson,
            "next_lesson": next_lesson,
            "is_admin": is_admin,
            # "exercises": exercises,
        },
    )