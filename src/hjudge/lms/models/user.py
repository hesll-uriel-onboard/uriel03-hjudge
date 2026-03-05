import secrets
import string
import uuid
from datetime import datetime
from hashlib import sha256

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from hjudge.commons.models import Base


class User(Base):
    """Represents a user in the database"""

    __tablename__ = "User"

    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]  # hashed
    name: Mapped[str]


class UserSession(Base):
    """Represents a session in the database"""

    __tablename__ = "UserSession"

    user: Mapped["User"] = mapped_column(ForeignKey("User.id"))
    cookie: Mapped[str] = mapped_column(
        unique=True, default_factory=lambda: UserSession.create_cookie()
    )
    issued_at: Mapped[datetime] = mapped_column(
        default_factory=lambda: datetime.now()
    )
    active: Mapped[bool] = mapped_column(default=True)

    @staticmethod
    def create_cookie() -> str:
        COOKIE_LENGTH = 30
        ALPHABET = string.ascii_letters + string.digits
        return "".join([secrets.choice(ALPHABET) for _ in range(COOKIE_LENGTH)])


def hashed_password(password: str) -> str:
    return sha256(password.encode()).hexdigest()
