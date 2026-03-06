import secrets
import string
from datetime import datetime
from hashlib import sha256
from typing import Self

import pydantic

from hjudge.commons.models import Base


def hashed_password(password: str) -> str:
    return sha256(password.encode()).hexdigest()


class User(Base):
    """Represents a user in the database"""

    username: str
    password: str  # hashed
    name: str

    def login(self) -> Self:
        self.password = hashed_password(self.password)
        return self


class UserSession(Base):
    """Represents a session in the database"""

    user: User
    cookie: str = pydantic.Field(
        default_factory=lambda: UserSession.create_cookie()
    )
    issued_at: datetime = pydantic.Field(default_factory=lambda: datetime.now())
    active: bool = pydantic.Field(default=True)

    @staticmethod
    def create_cookie() -> str:
        COOKIE_LENGTH = 30
        ALPHABET = string.ascii_letters + string.digits
        return "".join([secrets.choice(ALPHABET) for _ in range(COOKIE_LENGTH)])
