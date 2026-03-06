from dataclasses import dataclass
from typing import Generic, TypeVar

import litestar
import litestar.datastructures

from hjudge.commons.errors import AbstractError

T = TypeVar("T")


@dataclass
class AbstractResponse(Generic[T]):
    status_code: int
    cookies: dict[str, str] | None = None
    content: T | str = ""
    pass


class ErrorResponse(AbstractResponse):
    def __init__(self, error: AbstractError) -> None:
        super().__init__(status_code=error.code, content=error.msg)


def get_litestar_response(response: AbstractResponse):
    cookies = (
        None
        if response.cookies is None
        else [
            litestar.datastructures.Cookie(key=key, value=value)
            for key, value in response.cookies.items()
        ]
    )
    return litestar.Response(
        status_code=response.status_code,
        cookies=cookies,
        content=response.content,
    )
