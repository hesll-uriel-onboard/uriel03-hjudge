from hjudge.commons.endpoints.responses import AbstractResponse
from hjudge.commons.endpoints.status_codes import (
    HTTP_200_OK,
    HTTP_201_CREATED,
)
from hjudge.lms.models.course import Course, Lesson


class CourseResponse(AbstractResponse):
    def __init__(self, course: Course):
        super().__init__(status_code=HTTP_200_OK, content=course.model_dump(mode='json'))


class LessonResponse(AbstractResponse):
    def __init__(self, lesson: Lesson):
        super().__init__(status_code=HTTP_200_OK, content=lesson.model_dump(mode='json'))


class CourseListResponse(AbstractResponse):
    def __init__(self, courses: list[Course]):
        super().__init__(
            status_code=HTTP_200_OK,
            content={"courses": [c.model_dump(mode='json') for c in courses]},
        )


class LessonListResponse(AbstractResponse):
    def __init__(self, lessons: list[Lesson]):
        super().__init__(
            status_code=HTTP_200_OK,
            content={"lessons": [l.model_dump(mode='json') for l in lessons]},
        )


class CreateCourseResponse(AbstractResponse):
    def __init__(self, course: Course):
        super().__init__(status_code=HTTP_201_CREATED, content=course.model_dump(mode='json'))


class CreateLessonResponse(AbstractResponse):
    def __init__(self, lesson: Lesson):
        super().__init__(status_code=HTTP_201_CREATED, content=lesson.model_dump(mode='json'))


class SuccessResponse(AbstractResponse):
    def __init__(self):
        super().__init__(status_code=HTTP_200_OK)