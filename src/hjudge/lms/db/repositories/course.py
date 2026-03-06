from typing import List
from uuid import UUID

from hjudge.commons.db import AbstractRepository
from hjudge.lms.models.course import Course, Lesson


class AbstractCourseRepository(AbstractRepository):
    def get_all_course(self) -> List[Course]:
        raise NotImplementedError

    def get_course(self, id: UUID) -> Course:
        raise NotImplementedError

    def get_lesson(self, id: UUID) -> Lesson:
        raise NotImplementedError

    def add_course(self, course: Course):
        raise NotImplementedError

    def add_lesson(self, lesson: Lesson):
        raise NotImplementedError

    def update_course(self, course: Course):
        raise NotImplementedError

    def update_lesson(self, lesson: Lesson):
        raise NotImplementedError
