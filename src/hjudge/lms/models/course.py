from uuid import UUID

import pydantic

from hjudge.commons.models import Base
from hjudge.lms.models.user import User


class ContentBase(Base):
    title: str
    content: str
    slug: str


class Course(ContentBase):
    pass
    # lessons: list["Lesson"] = pydantic.Field(default_factory=list)


class Lesson(ContentBase):
    course: Course
    order: int
    exercise_ids: list[UUID] = pydantic.Field(default_factory=list)


class CourseAdmins(Base):
    course: Course
    users: list[User] = pydantic.Field(default_factory=list)
