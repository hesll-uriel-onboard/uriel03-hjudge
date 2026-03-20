from hjudge.commons.endpoints.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)
from hjudge.commons.errors import AbstractError


class JudgeNotExistedError(AbstractError):
    """Judge not existed"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_400_BAD_REQUEST, "Judge not existed", *args)


class ExerciseNotFoundError(AbstractError):
    """Exercise not found"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_404_NOT_FOUND, "Exercise not found", *args)


class SubmissionNotFoundError(AbstractError):
    """Exercise not found"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_404_NOT_FOUND, "Submission not found", *args)


class CodeforcesContestNotFoundError(AbstractError):
    """Codeforcs not found"""

    def __init__(self, *args: object) -> None:
        super().__init__(
            HTTP_404_NOT_FOUND, "Codeforces contest not found", *args
        )


class DmojProblemNotFoundError(AbstractError):
    """DMOJ problem not found"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_404_NOT_FOUND, "DMOJ problem not found", *args)


class AtcoderProblemNotFoundError(AbstractError):
    """AtCoder problem not found"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_404_NOT_FOUND, "AtCoder problem not found", *args)


class QojProblemNotFoundError(AbstractError):
    """QOJ problem not found"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_404_NOT_FOUND, "QOJ problem not found", *args)
