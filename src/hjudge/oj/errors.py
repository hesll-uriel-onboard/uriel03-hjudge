from hjudge.commons.endpoints.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)
from hjudge.commons.errors import AbstractError


class JudgeNotExistedError(AbstractError):
    """Judge not existed"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_400_BAD_REQUEST, "Judge not existed", *args)


class ExerciseNotFoundError(Exception):
    """Exercise not found"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_404_NOT_FOUND, "Exercise not found", *args)
