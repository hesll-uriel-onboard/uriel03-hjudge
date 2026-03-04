import secrets
import string
from datetime import datetime
from typing import Protocol, override
from uuid import uuid4

from pydantic import UUID4
from sqlalchemy import Result, Row, insert
from sqlalchemy.orm import Session

from hjudge.lms.db.repositories import AbstractRepository
from hjudge.lms.db.tables.user import user_session_table, user_table
from hjudge.lms.models.user import User, UserSession


# Main class
class AbstractUserRepository(AbstractRepository):
    """
    A repository to manage
    """

    # main functionalities
    def get_user(self, username: str) -> User | None:
        raise NotImplementedError

    def add_user(self, user: User):
        raise NotImplementedError

    def get_user_session(self, cookie: str) -> UserSession | None:
        raise NotImplementedError

    def add_user_session(self, user_session: UserSession):
        raise NotImplementedError


class SQLAlchemyUserRepository(AbstractUserRepository):
    session: Session

    def __init__(self, session) -> None:
        super().__init__()
        self.session = session

    def get_user(self, username: str) -> User | None:
        return (
            self.session.query(User).filter_by(username=username).one_or_none()
        )

    def add_user(self, user: User):
        self.session.add(user)

    def get_user_session(self, cookie: str) -> UserSession | None:
        return (
            self.session.query(UserSession)
            .filter_by(cookie=cookie)
            .one_or_none()
        )

    def add_user_session(self, user_session: UserSession):
        self.session.add(user_session)
