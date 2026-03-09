from uuid import UUID

from hjudge.commons.models import Base, entity_dumps
from hjudge.lms.db.entities.user import UserSessionEntity
from hjudge.lms.models.user import User, UserSession


def test_entity_dumps():
    class A(Base):
        x: int
        pass

    class B(Base):
        a: A
        y: str

    b = B(a=A(x=2), y="a")
    dump = entity_dumps(b)
    print(dump)
    assert isinstance(dump["id"], UUID)
    assert isinstance(dump["a_id"], UUID)
    assert isinstance(dump["y"], str)


def test_as_entity():
    user = User(username="a", password="b", name="c")
    user_session = UserSession(user=user)
    user_session_entity = UserSessionEntity.from_model(user_session)
    assert user_session_entity.id == user_session.id
    assert user_session_entity.user_id == user.id
    assert user_session_entity.issued_at == user_session.issued_at
    assert user_session_entity.cookie == user_session.cookie
    assert user_session_entity.active == user_session.active
