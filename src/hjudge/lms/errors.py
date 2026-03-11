############## User ##############
from litestar.status_codes import HTTP_401_UNAUTHORIZED

from hjudge.commons.endpoints.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_409_CONFLICT,
)
from hjudge.commons.errors import AbstractError, InternalError


class UserExistedError(AbstractError):
    """User existed"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_409_CONFLICT, "User existed.", *args)


class UserNotFoundError(AbstractError):
    """User not found"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_400_BAD_REQUEST, "Wrong credentials.", *args)


class UserWrongPasswordError(AbstractError):
    """Login with wrong credential"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_400_BAD_REQUEST, "Wrong credentials.", *args)


class CookieExistedError(InternalError):
    """Cookie existed"""

    def __init__(
        self, msg: str = "Internal Server Error", *args: object
    ) -> None:
        super().__init__(msg, *args)


class NotAuthorizedError(AbstractError):
    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_401_UNAUTHORIZED, "Not authorized.", *args)


############## Course ##############

class CourseNotFoundError(AbstractError):
    """Course not found"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_400_BAD_REQUEST, "Course not found.", *args)


class CourseSlugExistsError(AbstractError):
    """Course slug already exists"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_409_CONFLICT, "Course slug already exists.", *args)


class LessonSlugExistsError(AbstractError):
    """Lesson slug already exists in this course"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_409_CONFLICT, "Lesson slug already exists in this course.", *args)


class NotCourseAdminError(AbstractError):
    """User is not an admin of this course"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_401_UNAUTHORIZED, "Not a course admin.", *args)


class CannotRemoveLastAdminError(AbstractError):
    """Cannot remove the last admin of a course"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_400_BAD_REQUEST, "Cannot remove the last admin.", *args)
