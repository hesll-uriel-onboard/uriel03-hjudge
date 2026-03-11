from uuid import UUID

from hjudge.commons.db.repositories import (
    AbstractRepository,
    SQLAlchemyAbstractRepository,
)
from hjudge.lms.db.entities.course import CourseAdminEntity, CourseEntity, LessonEntity
from hjudge.lms.db.entities.user import UserEntity


class AbstractCourseRepository(AbstractRepository):
    """A repository to manage courses."""

    def get_course(self, course_id: UUID) -> CourseEntity | None:
        raise NotImplementedError

    def get_course_by_slug(self, slug: str) -> CourseEntity | None:
        raise NotImplementedError

    def add_course(self, course: CourseEntity) -> None:
        raise NotImplementedError

    def list_courses(self) -> list[CourseEntity]:
        raise NotImplementedError


class AbstractLessonRepository(AbstractRepository):
    """A repository to manage lessons."""

    def get_lesson(self, lesson_id: UUID) -> LessonEntity | None:
        raise NotImplementedError

    def get_lesson_by_slug(self, course_slug: str, lesson_slug: str) -> LessonEntity | None:
        raise NotImplementedError

    def add_lesson(self, lesson: LessonEntity) -> None:
        raise NotImplementedError

    def list_lessons_by_course(self, course_id: UUID) -> list[LessonEntity]:
        raise NotImplementedError


class AbstractCourseAdminRepository(AbstractRepository):
    """A repository to manage course admins."""

    def is_admin(self, course_id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError

    def add_admin(self, course_id: UUID, user_id: UUID) -> None:
        raise NotImplementedError

    def remove_admin(self, course_id: UUID, user_id: UUID) -> None:
        raise NotImplementedError

    def list_admins(self, course_id: UUID) -> list[UserEntity]:
        raise NotImplementedError


class SQLAlchemyCourseRepository(
    SQLAlchemyAbstractRepository, AbstractCourseRepository
):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get_course(self, course_id: UUID) -> CourseEntity | None:
        return (
            self.session.query(CourseEntity)
            .filter_by(id=course_id)
            .one_or_none()
        )

    def get_course_by_slug(self, slug: str) -> CourseEntity | None:
        return (
            self.session.query(CourseEntity)
            .filter_by(slug=slug)
            .one_or_none()
        )

    def add_course(self, course: CourseEntity) -> None:
        self.session.add(course)

    def list_courses(self) -> list[CourseEntity]:
        return self.session.query(CourseEntity).all()


class SQLAlchemyLessonRepository(
    SQLAlchemyAbstractRepository, AbstractLessonRepository
):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get_lesson(self, lesson_id: UUID) -> LessonEntity | None:
        return (
            self.session.query(LessonEntity)
            .filter_by(id=lesson_id)
            .one_or_none()
        )

    def get_lesson_by_slug(self, course_slug: str, lesson_slug: str) -> LessonEntity | None:
        return (
            self.session.query(LessonEntity)
            .join(CourseEntity)
            .filter(CourseEntity.slug == course_slug)
            .filter(LessonEntity.slug == lesson_slug)
            .one_or_none()
        )

    def add_lesson(self, lesson: LessonEntity) -> None:
        self.session.add(lesson)

    def list_lessons_by_course(self, course_id: UUID) -> list[LessonEntity]:
        return (
            self.session.query(LessonEntity)
            .filter_by(course_id=course_id)
            .order_by(LessonEntity.order)
            .all()
        )


class SQLAlchemyCourseAdminRepository(
    SQLAlchemyAbstractRepository, AbstractCourseAdminRepository
):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def is_admin(self, course_id: UUID, user_id: UUID) -> bool:
        return (
            self.session.query(CourseAdminEntity)
            .filter_by(course_id=course_id, user_id=user_id)
            .first()
            is not None
        )

    def add_admin(self, course_id: UUID, user_id: UUID) -> None:
        admin = CourseAdminEntity(course_id=course_id, user_id=user_id)
        self.session.add(admin)

    def remove_admin(self, course_id: UUID, user_id: UUID) -> None:
        self.session.query(CourseAdminEntity).filter_by(
            course_id=course_id, user_id=user_id
        ).delete()

    def list_admins(self, course_id: UUID) -> list[UserEntity]:
        return (
            self.session.query(UserEntity)
            .join(CourseAdminEntity, CourseAdminEntity.user_id == UserEntity.id)
            .filter(CourseAdminEntity.course_id == course_id)
            .all()
        )