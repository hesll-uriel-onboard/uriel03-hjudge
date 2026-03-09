import abc

from hjudge.commons.endpoints.status_codes import HTTP_500_INTERNAL_SERVER_ERROR


class AbstractError(Exception, abc.ABC):
    code: int
    msg: str

    @abc.abstractmethod
    def __init__(self, code: int, msg: str, *args: object) -> None:
        self.code = code
        self.msg = msg
        super().__init__(*args)


class InternalError(AbstractError):
    @abc.abstractmethod
    def __init__(
        self, msg: str = "Internal Server Error", *args: object
    ) -> None:
        super().__init__(HTTP_500_INTERNAL_SERVER_ERROR, msg, *args)


############## UOW ##############
class UOWSessionNotFoundError(InternalError):
    """`current_session` is None"""

    def __init__(self, *args: object) -> None:
        super().__init__("User not found", *args)
