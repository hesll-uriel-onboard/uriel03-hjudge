"""Convert entity -> model and model -> entity"""

from hjudge.lms.db.entities.user import UserEntity, UserSessionEntity
from hjudge.lms.models.user import User, UserSession


def as_user_entity(user: User) -> UserEntity:
    return UserEntity(
        id=user.id,
        username=user.username,
        password=user.password,
        name=user.name,
    )


def as_user_session_entity(user_session: UserSession) -> UserSessionEntity:
    return UserSessionEntity(
        id=user_session.id,
        user_id=user_session.user.id,
        cookie=user_session.cookie,
        issued_at=user_session.issued_at,
        active=user_session.active,
    )
