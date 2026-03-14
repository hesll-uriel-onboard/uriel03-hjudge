from uuid import UUID

from litestar import Request, Response, delete, get, patch, post

from hjudge.commons.db.uow import AbstractUOWFactory
from hjudge.commons.endpoints.responses import (
    AbstractResponse,
    ErrorResponse,
    get_litestar_response,
)
from hjudge.commons.errors import AbstractError
from hjudge.lms.endpoints.authentication import authenticate_user
from hjudge.lms.endpoints.requests.course import (
    AddAdminRequest,
    CreateCourseRequest,
    CreateLessonRequest,
    UpdateCourseRequest,
    UpdateLessonRequest,
)
from hjudge.lms.endpoints.responses.course import (
    CourseListResponse,
    CourseResponse,
    CreateCourseResponse,
    CreateLessonResponse,
    LessonListResponse,
    LessonResponse,
    SuccessResponse,
)
from hjudge.lms.endpoints.responses.user import COOKIE_KEY
from hjudge.lms.errors import CourseNotFoundError, NotAuthorizedError
from hjudge.lms.services import course as course_services


@post("/api/courses")
async def create_course(
    request: Request,
    uow_factory: AbstractUOWFactory,
    data: CreateCourseRequest,
) -> Response:
    response: AbstractResponse
    try:
        cookie = request.cookies.get(COOKIE_KEY)
        user = authenticate_user(cookie, uow_factory.create_uow(), required=True)
        if user is None:
            raise NotAuthorizedError()

        course = course_services.create_course(
            title=data.title,
            content=data.content,
            slug=data.slug,
            creator_user_id=user.id,
            uow=uow_factory.create_uow(),
        )
        response = CreateCourseResponse(course)
    except AbstractError as e:
        response = ErrorResponse(e)

    return get_litestar_response(response)


@get("/api/courses")
async def list_courses(uow_factory: AbstractUOWFactory) -> Response:
    courses = course_services.list_courses(uow_factory.create_uow())
    return get_litestar_response(CourseListResponse(courses))


@get("/api/courses/{slug:str}")
async def get_course(uow_factory: AbstractUOWFactory, slug: str) -> Response:
    response: AbstractResponse
    course = course_services.get_course_by_slug(slug, uow_factory.create_uow())
    if course is None:
        response = ErrorResponse(CourseNotFoundError())
    else:
        response = CourseResponse(course)
    return get_litestar_response(response)


@patch("/api/courses/{slug:str}")
async def update_course(
    request: Request,
    uow_factory: AbstractUOWFactory,
    slug: str,
    data: UpdateCourseRequest,
) -> Response:
    response: AbstractResponse
    try:
        cookie = request.cookies.get(COOKIE_KEY)
        user = authenticate_user(cookie, uow_factory.create_uow(), required=True)
        if user is None:
            raise NotAuthorizedError()

        course = course_services.get_course_by_slug(slug, uow_factory.create_uow())
        if course is None:
            raise CourseNotFoundError()

        updated = course_services.update_course(
            course_id=course.id,
            title=data.title,
            content=data.content,
            user_id=user.id,
            uow=uow_factory.create_uow(),
        )
        response = CourseResponse(updated)
    except AbstractError as e:
        response = ErrorResponse(e)

    return get_litestar_response(response)


@post("/api/courses/{slug:str}/lessons")
async def create_lesson(
    request: Request,
    uow_factory: AbstractUOWFactory,
    slug: str,
    data: CreateLessonRequest,
) -> Response:
    response: AbstractResponse
    try:
        cookie = request.cookies.get(COOKIE_KEY)
        user = authenticate_user(cookie, uow_factory.create_uow(), required=True)
        if user is None:
            raise NotAuthorizedError()

        course = course_services.get_course_by_slug(slug, uow_factory.create_uow())
        if course is None:
            raise CourseNotFoundError()

        lesson = course_services.create_lesson(
            course_id=course.id,
            title=data.title,
            content=data.content,
            slug=data.slug,
            exercise_ids=data.exercise_ids,
            user_id=user.id,
            uow=uow_factory.create_uow(),
        )
        response = CreateLessonResponse(lesson)
    except AbstractError as e:
        response = ErrorResponse(e)

    return get_litestar_response(response)


@get("/api/courses/{slug:str}/lessons")
async def list_lessons(uow_factory: AbstractUOWFactory, slug: str) -> Response:
    course = course_services.get_course_by_slug(slug, uow_factory.create_uow())
    if course is None:
        return get_litestar_response(ErrorResponse(CourseNotFoundError()))

    lessons = course_services.list_lessons(course.id, uow_factory.create_uow())
    return get_litestar_response(LessonListResponse(lessons))


@get("/api/courses/{course_slug:str}/lessons/{lesson_slug:str}")
async def get_lesson(
    uow_factory: AbstractUOWFactory, course_slug: str, lesson_slug: str
) -> Response:
    response: AbstractResponse
    lesson = course_services.get_lesson_by_slug(
        course_slug, lesson_slug, uow_factory.create_uow()
    )
    if lesson is None:
        response = ErrorResponse(CourseNotFoundError())
    else:
        response = LessonResponse(lesson)
    return get_litestar_response(response)


@patch("/api/courses/{course_slug:str}/lessons/{lesson_slug:str}")
async def update_lesson(
    request: Request,
    uow_factory: AbstractUOWFactory,
    course_slug: str,
    lesson_slug: str,
    data: UpdateLessonRequest,
) -> Response:
    response: AbstractResponse
    try:
        cookie = request.cookies.get(COOKIE_KEY)
        user = authenticate_user(cookie, uow_factory.create_uow(), required=True)
        if user is None:
            raise NotAuthorizedError()

        lesson = course_services.get_lesson_by_slug(
            course_slug, lesson_slug, uow_factory.create_uow()
        )
        if lesson is None:
            raise CourseNotFoundError()

        updated = course_services.update_lesson(
            lesson_id=lesson.id,
            title=data.title,
            content=data.content,
            exercise_ids=data.exercise_ids,
            user_id=user.id,
            uow=uow_factory.create_uow(),
        )
        response = LessonResponse(updated)
    except AbstractError as e:
        response = ErrorResponse(e)

    return get_litestar_response(response)


@post("/api/courses/{slug:str}/admins")
async def add_admin(
    request: Request,
    uow_factory: AbstractUOWFactory,
    slug: str,
    data: AddAdminRequest,
) -> Response:
    response: AbstractResponse
    try:
        cookie = request.cookies.get(COOKIE_KEY)
        user = authenticate_user(cookie, uow_factory.create_uow(), required=True)
        if user is None:
            raise NotAuthorizedError()

        course = course_services.get_course_by_slug(slug, uow_factory.create_uow())
        if course is None:
            raise CourseNotFoundError()

        course_services.add_course_admin(
            course_id=course.id,
            new_admin_user_id=data.user_id,
            requester_user_id=user.id,
            uow=uow_factory.create_uow(),
        )
        response = SuccessResponse()
    except AbstractError as e:
        response = ErrorResponse(e)

    return get_litestar_response(response)


@delete("/api/courses/{slug:str}/admins/{user_id:str}", status_code=200)
async def remove_admin(
    request: Request,
    uow_factory: AbstractUOWFactory,
    slug: str,
    user_id: str,
) -> Response:
    response: AbstractResponse
    try:
        cookie = request.cookies.get(COOKIE_KEY)
        requester = authenticate_user(cookie, uow_factory.create_uow(), required=True)
        if requester is None:
            raise NotAuthorizedError()

        course = course_services.get_course_by_slug(slug, uow_factory.create_uow())
        if course is None:
            raise CourseNotFoundError()

        course_services.remove_course_admin(
            course_id=course.id,
            admin_user_id=UUID(user_id),
            requester_user_id=requester.id,
            uow=uow_factory.create_uow(),
        )
        response = SuccessResponse()
    except AbstractError as e:
        response = ErrorResponse(e)

    return get_litestar_response(response)