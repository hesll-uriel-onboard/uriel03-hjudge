from sqlalchemy.orm import Session

from hjudge.commons.db import AbstractRepository, SQLAlchemyAbstractRepository
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


class SQLAlchemyUserRepository(
    SQLAlchemyAbstractRepository, AbstractUserRepository
):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

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
