from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.lms.db.repositories.user import AbstractUserRepository
from hjudge.lms.errors import (
    UserExistedError,
    UserNotFoundError,
    UserWrongPasswordError,
)
from hjudge.lms.models.entity_converter import (
    as_user_entity,
    as_user_session_entity,
)
from hjudge.lms.models.user import User, UserSession, hashed_password


def register(
    username: str, password: str, name: str, uow: AbstractUnitOfWork
) -> User:
    password = hashed_password(password)
    with uow:
        user_repo: AbstractUserRepository = uow.create_repository(
            AbstractUserRepository
        )  # pyright: ignore
        if user_repo.get_user(username) is not None:
            raise UserExistedError

        user = User(username=username, password=password, name=name)
        user_repo.add_user(as_user_entity(user))

        uow.commit()

    return user


def login(username: str, password: str, uow: AbstractUnitOfWork) -> UserSession:
    # TODO after MVP: disable usersession after a month
    with uow:
        user_repo: AbstractUserRepository = uow.create_repository(
            AbstractUserRepository
        )  # pyright: ignore

        user_entity = user_repo.get_user(username)
        if user_entity is None:
            raise UserNotFoundError
        user = user_entity.as_model()

        if user.password != hashed_password(password):
            raise UserWrongPasswordError

        user_session = UserSession(user=user)
        user_repo.add_user_session(as_user_session_entity(user_session))

        uow.commit()
    return user_session
