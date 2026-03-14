"""Represents"""

from typing import override
from uuid import UUID

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hjudge.commons.db.entities import BaseEntity
from hjudge.lms.db.entities.user import UserEntity
from hjudge.lms.models.course import Course, Lesson


class CourseEntity(BaseEntity):
    """Represents a course"""

    __tablename__ = "Course"

    title: Mapped[str]
    content: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)
    # lessons: Mapped[list["LessonEntity"]] = relationship(
    #     back_populates="course",
    #     init=False,
    #     order_by="LessonEntity.order",
    # )

    @override
    def as_model(self, **kwargs) -> Course:
        return Course(
            id=self.id,
            title=self.title,
            content=self.content,
            slug=self.slug,
        )


class LessonEntity(BaseEntity):
    """Represents a lesson"""

    __tablename__ = "Lesson"

    title: Mapped[str]
    content: Mapped[str]
    slug: Mapped[str]
    course_id: Mapped[UUID] = mapped_column(ForeignKey("Course.id"))
    course: Mapped["CourseEntity"] = relationship(init=False)
    order: Mapped[int]
    exercise_ids: Mapped[list[str]] = mapped_column(JSON, default_factory=list)

    @override
    def as_model(self, **kwargs) -> Lesson:
        return Lesson(
            id=self.id,
            title=self.title,
            content=self.content,
            slug=self.slug,
            course=self.course.as_model(),
            order=self.order,
            exercise_ids=[UUID(id) for id in self.exercise_ids],
        )


class CourseAdminEntity(BaseEntity):
    """Represents a course admin"""

    __tablename__ = "CourseAdmin"

    course_id: Mapped[UUID] = mapped_column(ForeignKey("Course.id"))
    course: Mapped["CourseEntity"] = relationship(init=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("User.id"))
    user: Mapped["UserEntity"] = relationship(init=False)
