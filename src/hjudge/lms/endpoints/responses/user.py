from hjudge.commons.endpoints.responses import AbstractResponse
from hjudge.commons.endpoints.status_codes import (
    HTTP_200_OK,
    HTTP_201_CREATED,
)

COOKIE_KEY = "cookie"


class UserLoginResponse(AbstractResponse):
    def __init__(self, cookie: str):
        super().__init__(status_code=HTTP_200_OK, cookies={COOKIE_KEY: cookie})


class UserRegisterResponse(AbstractResponse):
    def __init__(self):
        super().__init__(status_code=HTTP_201_CREATED)
