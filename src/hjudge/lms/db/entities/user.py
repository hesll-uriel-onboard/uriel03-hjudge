"""Represents"""

from datetime import datetime
from typing import override
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hjudge.commons.db.entities import BaseEntity
from hjudge.lms.models.user import User, UserSession


class UserEntity(BaseEntity):
    """Represents a user in the database"""

    __tablename__ = "User"

    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]  # hashed
    name: Mapped[str]

    @override
    def as_model(self, **kwargs) -> User:
        return User(
            id=self.id,
            username=self.username,
            password=self.password,
            name=self.name,
        )


class UserSessionEntity(BaseEntity):
    """Represents a session in the database"""

    __tablename__ = "UserSession"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("User.id"))
    user: Mapped["UserEntity"] = relationship(init=False)
    cookie: Mapped[str] = mapped_column(unique=True)
    issued_at: Mapped[datetime]
    active: Mapped[bool]

    @override
    def as_model(self, **kwargs) -> UserSession:
        return UserSession(
            id=self.id,
            user=self.user.as_model(),
            cookie=self.cookie,
            issued_at=self.issued_at,
            active=self.active,
        )
