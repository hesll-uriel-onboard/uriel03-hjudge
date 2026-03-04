from hjudge.lms.db.repositories.user import AbstractUserRepository
from hjudge.lms.db.uow import AbstractUnitOfWork
from hjudge.lms.errors import (
    UserExistedError,
    UserNotFoundError,
    UserWrongPasswordError,
)
from hjudge.lms.models.user import User, UserSession


def register(
    username: str, password: str, name: str, uow: AbstractUnitOfWork
) -> User:
    with uow:
        user_repo: AbstractUserRepository = uow.create_repository(
            AbstractUserRepository
        )  # pyright: ignore
        if user_repo.get_user(username) is not None:
            raise UserExistedError

        user = User(username=username, password=password, name=name)
        user_repo.add_user(user)

        uow.commit()

    return user


def login(username: str, password: str, uow: AbstractUnitOfWork) -> UserSession:
    # TODO after MVP: disable usersession after a month
    with uow:
        user_repo: AbstractUserRepository = uow.create_repository(
            AbstractUserRepository
        )  # pyright: ignore

        user = user_repo.get_user(username)
        if user is None:
            raise UserNotFoundError
        print("====================")
        print(user.username, username)
        print(user.password, password)
        print("====================")
        if user.password != password:
            raise UserWrongPasswordError

        user_session = UserSession(user=user)
        user_repo.add_user_session(user_session)

        pass
    return user_session
