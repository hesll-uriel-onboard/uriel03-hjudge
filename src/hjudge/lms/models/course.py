from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from hjudge.commons.models import Base


class ContentBase(Base, DeclarativeBase):
    title: Mapped[str]
    content: Mapped[str]


class Course(ContentBase):
    __tablename__ = "Course"

    lessons: Mapped[List["Lesson"]] = relationship(back_populates="Lesson")


class Lesson(ContentBase):
    __tablename__ = "Lesson"
    course: Mapped["Course"] = mapped_column(ForeignKey("Course.id"))


class LessonExercise(ContentBase):
    __tablename__ = "LessonExercise"
    course: Mapped["Course"] = mapped_column(ForeignKey("Course.id"))


print(Course.__table__.schema)
print(Lesson.__table__.schema)
