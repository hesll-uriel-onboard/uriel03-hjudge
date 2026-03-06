############## User ##############
from hjudge.commons.endpoints.status_codes import HTTP_400_BAD_REQUEST
from hjudge.commons.errors import AbstractError, InternalError


class UserExistedError(AbstractError):
    """User existed"""

    def __init__(self, *args: object) -> None:
        super().__init__(HTTP_400_BAD_REQUEST, "User existed.", *args)


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
