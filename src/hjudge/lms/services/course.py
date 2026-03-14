from uuid import UUID

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.db.entities.course import CourseAdminEntity, CourseEntity, LessonEntity
from hjudge.lms.db.repositories.course import (
    AbstractCourseAdminRepository,
    AbstractCourseRepository,
    AbstractLessonRepository,
)
from hjudge.lms.errors import (
    CannotRemoveLastAdminError,
    CourseNotFoundError,
    CourseSlugExistsError,
    LessonSlugExistsError,
    NotCourseAdminError,
)
from hjudge.lms.models.course import Course, Lesson


def create_course(
    title: str,
    content: str,
    slug: str,
    creator_user_id: UUID,
    uow: AbstractUnitOfWork,
) -> Course:
    """Create a course. Creator becomes the first admin."""
    with uow:
        course_repo: AbstractCourseRepository = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore
        admin_repo: AbstractCourseAdminRepository = uow.create_repository(
            AbstractCourseAdminRepository
        )  # pyright: ignore

        # Check if slug already exists
        if course_repo.get_course_by_slug(slug) is not None:
            raise CourseSlugExistsError

        # Create course
        course = Course(title=title, content=content, slug=slug)
        course_repo.add_course(CourseEntity.from_model(course))
        uow.commit()

        # Get the created course to get its ID
        course_entity = course_repo.get_course_by_slug(slug)
        assert course_entity is not None

        # Make creator an admin
        admin_repo.add_admin(course_entity.id, creator_user_id)
        uow.commit()

        return course_entity.as_model()


def update_course(
    course_id: UUID,
    title: str,
    content: str,
    user_id: UUID,
    uow: AbstractUnitOfWork,
) -> Course:
    """Update course. Must be admin."""
    with uow:
        course_repo: AbstractCourseRepository = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore
        admin_repo: AbstractCourseAdminRepository = uow.create_repository(
            AbstractCourseAdminRepository
        )  # pyright: ignore

        # Check if user is admin
        if not admin_repo.is_admin(course_id, user_id):
            raise NotCourseAdminError

        # Get course
        course_entity = course_repo.get_course(course_id)
        if course_entity is None:
            raise CourseNotFoundError

        # Update fields
        course_entity.title = title
        course_entity.content = content
        uow.commit()

        return course_entity.as_model()


def create_lesson(
    course_id: UUID,
    title: str,
    content: str,
    slug: str,
    exercise_ids: list[UUID],
    user_id: UUID,
    uow: AbstractUnitOfWork,
) -> Lesson:
    """Create a lesson in a course. Must be course admin."""
    with uow:
        course_repo: AbstractCourseRepository = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore
        lesson_repo: AbstractLessonRepository = uow.create_repository(
            AbstractLessonRepository
        )  # pyright: ignore
        admin_repo: AbstractCourseAdminRepository = uow.create_repository(
            AbstractCourseAdminRepository
        )  # pyright: ignore

        # Check if user is admin
        if not admin_repo.is_admin(course_id, user_id):
            raise NotCourseAdminError

        # Check if course exists
        course_entity = course_repo.get_course(course_id)
        if course_entity is None:
            raise CourseNotFoundError

        # Check if slug already exists in this course
        course_slug = course_entity.slug
        if lesson_repo.get_lesson_by_slug(course_slug, slug) is not None:
            raise LessonSlugExistsError

        # Determine order (next available)
        existing_lessons = lesson_repo.list_lessons_by_course(course_id)
        order = len(existing_lessons) + 1

        # Convert UUIDs to strings for storage
        exercise_id_strings = [str(eid) for eid in exercise_ids]

        # Create lesson
        lesson = Lesson(
            title=title,
            content=content,
            slug=slug,
            course=course_entity.as_model(),
            order=order,
            exercise_ids=exercise_ids,
        )
        lesson_entity = LessonEntity(
            title=title,
            content=content,
            slug=slug,
            course_id=course_id,
            order=order,
            exercise_ids=exercise_id_strings,
        )
        lesson_repo.add_lesson(lesson_entity)
        uow.commit()

        # Get the created lesson
        created = lesson_repo.get_lesson_by_slug(course_slug, slug)
        assert created is not None
        return created.as_model()


def get_course(course_id: UUID, uow: AbstractUnitOfWork) -> Course | None:
    """Get a course by ID."""
    with uow:
        course_repo: AbstractCourseRepository = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore

        course_entity = course_repo.get_course(course_id)
        if course_entity is None:
            return None
        return course_entity.as_model()


def get_course_by_slug(slug: str, uow: AbstractUnitOfWork) -> Course | None:
    """Get a course by slug."""
    with uow:
        course_repo: AbstractCourseRepository = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore

        course_entity = course_repo.get_course_by_slug(slug)
        if course_entity is None:
            return None
        return course_entity.as_model()


def get_lesson_by_slug(
    course_slug: str, lesson_slug: str, uow: AbstractUnitOfWork
) -> Lesson | None:
    """Get a lesson by course slug and lesson slug."""
    with uow:
        lesson_repo: AbstractLessonRepository = uow.create_repository(
            AbstractLessonRepository
        )  # pyright: ignore

        lesson_entity = lesson_repo.get_lesson_by_slug(course_slug, lesson_slug)
        if lesson_entity is None:
            return None
        return lesson_entity.as_model()


def update_lesson(
    lesson_id: UUID,
    title: str,
    content: str,
    exercise_ids: list[UUID],
    user_id: UUID,
    uow: AbstractUnitOfWork,
) -> Lesson:
    """Update lesson. Must be course admin."""
    with uow:
        lesson_repo: AbstractLessonRepository = uow.create_repository(
            AbstractLessonRepository
        )  # pyright: ignore
        admin_repo: AbstractCourseAdminRepository = uow.create_repository(
            AbstractCourseAdminRepository
        )  # pyright: ignore

        # Get lesson
        lesson_entity = lesson_repo.get_lesson(lesson_id)
        if lesson_entity is None:
            raise CourseNotFoundError

        # Check if user is admin
        if not admin_repo.is_admin(lesson_entity.course_id, user_id):
            raise NotCourseAdminError

        # Update fields
        lesson_entity.title = title
        lesson_entity.content = content
        lesson_entity.exercise_ids = [str(eid) for eid in exercise_ids]
        uow.commit()

        return lesson_entity.as_model()


def list_courses(uow: AbstractUnitOfWork) -> list[Course]:
    """List all courses."""
    with uow:
        course_repo: AbstractCourseRepository = uow.create_repository(
            AbstractCourseRepository
        )  # pyright: ignore

        course_entities = course_repo.list_courses()
        return [e.as_model() for e in course_entities]


def list_lessons(course_id: UUID, uow: AbstractUnitOfWork) -> list[Lesson]:
    """List all lessons in a course, ordered by order field."""
    with uow:
        lesson_repo: AbstractLessonRepository = uow.create_repository(
            AbstractLessonRepository
        )  # pyright: ignore

        lesson_entities = lesson_repo.list_lessons_by_course(course_id)
        return [e.as_model() for e in lesson_entities]


def is_admin(course_id: UUID, user_id: UUID, uow: AbstractUnitOfWork) -> bool:
    """Check if a user is an admin of a course."""
    with uow:
        admin_repo: AbstractCourseAdminRepository = uow.create_repository(
            AbstractCourseAdminRepository
        )  # pyright: ignore

        return admin_repo.is_admin(course_id, user_id)


def add_course_admin(
    course_id: UUID,
    new_admin_user_id: UUID,
    requester_user_id: UUID,
    uow: AbstractUnitOfWork,
) -> None:
    """Add an admin to a course. Must be existing admin."""
    with uow:
        admin_repo: AbstractCourseAdminRepository = uow.create_repository(
            AbstractCourseAdminRepository
        )  # pyright: ignore

        # Check if requester is admin
        if not admin_repo.is_admin(course_id, requester_user_id):
            raise NotCourseAdminError

        # Add new admin
        admin_repo.add_admin(course_id, new_admin_user_id)
        uow.commit()


def remove_course_admin(
    course_id: UUID,
    admin_user_id: UUID,
    requester_user_id: UUID,
    uow: AbstractUnitOfWork,
) -> None:
    """Remove an admin. Must be existing admin. Cannot remove last admin."""
    with uow:
        admin_repo: AbstractCourseAdminRepository = uow.create_repository(
            AbstractCourseAdminRepository
        )  # pyright: ignore

        # Check if requester is admin
        if not admin_repo.is_admin(course_id, requester_user_id):
            raise NotCourseAdminError

        # Check if this is the last admin
        admins = admin_repo.list_admins(course_id)
        if len(admins) <= 1:
            raise CannotRemoveLastAdminError

        # Remove admin
        admin_repo.remove_admin(course_id, admin_user_id)
        uow.commit()