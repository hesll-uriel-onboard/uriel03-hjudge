from hjudge.commons.db.repositories import (
    AbstractRepository,
    SQLAlchemyAbstractRepository,
)
from hjudge.lms.db.entities.user import UserEntity, UserSessionEntity


# Main class
class AbstractUserRepository(AbstractRepository):
    """
    A repository to manage
    """

    # main functionalities
    def get_user(self, username: str) -> UserEntity | None:
        raise NotImplementedError

    def add_user(self, user: UserEntity):
        raise NotImplementedError

    def get_user_session(self, cookie: str) -> UserSessionEntity | None:
        raise NotImplementedError

    def add_user_session(self, user_session: UserSessionEntity):
        raise NotImplementedError


class SQLAlchemyUserRepository(
    SQLAlchemyAbstractRepository, AbstractUserRepository
):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get_user(self, username: str) -> UserEntity | None:
        return (
            self.session.query(UserEntity)
            .filter_by(username=username)
            .one_or_none()
        )

    def add_user(self, user: UserEntity):
        self.session.add(user)

    def get_user_session(self, cookie: str) -> UserSessionEntity | None:
        return (
            self.session.query(UserSessionEntity)
            .filter_by(cookie=cookie)
            .one_or_none()
        )

    def add_user_session(self, user_session: UserSessionEntity):
        self.session.add(user_session)
