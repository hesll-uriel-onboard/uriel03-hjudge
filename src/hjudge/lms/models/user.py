import secrets
import string
import uuid
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    declared_attr,
    mapped_column,
)

from hjudge.lms.db.tables import mapper_registry

# @mapper_registry.as_declarative_base()
# class Base(BaseModel):
#     @declared_attr
#     def __tablename__(cls):
#         return cls.__name__.lower()  # pyright: ignore


#     id: UUID4 = Column(Integer, primary_key=True)
# @mapper_registry.as_declarative_base()
class Base(DeclarativeBase, MappedAsDataclass, kw_only=True):
    id: Mapped[UUID] = mapped_column(
        primary_key=True, default_factory=lambda: uuid.uuid4()
    )
    pass


class User(Base):
    """Represents a user in the database"""

    __tablename__ = "User"

    # Field(default_factory=lambda: uuid.uuid4())

    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]  # hashed
    name: Mapped[str]


def create_cookie() -> str:
    COOKIE_LENGTH = 30
    ALPHABET = string.ascii_letters + string.digits
    return "".join([secrets.choice(ALPHABET) for _ in range(COOKIE_LENGTH)])


class UserSession(Base):
    """Represents a session in the database"""

    __tablename__ = "UserSession"

    user: Mapped["User"] = mapped_column(ForeignKey("User.id"))
    cookie: Mapped[str] = mapped_column(
        unique=True, default_factory=lambda: create_cookie()
    )
    issued_at: Mapped[datetime] = mapped_column(
        default_factory=lambda: datetime.now()
    )
    active: Mapped[bool] = mapped_column(default=True)


# this is saved just in case i need pure orm
# class User(Base):
#     """Represents a user in the database"""

# __tablename__ = "User"

#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     username: Mapped[str] = mapped_column(unique=True)
#     password: Mapped[str]  # hashed
#     name: Mapped[str]


# class UserSession(Base):
#     """Represents a session in the database"""

#     __tablename__ = "UserSession"

#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     user: Mapped["User"] = mapped_column(ForeignKey("User.id"))
#     cookie: Mapped[str] = mapped_column(unique=True)
#     issued_at: Mapped[datetime]
#     active: Mapped[bool]
