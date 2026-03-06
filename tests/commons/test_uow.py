import pytest

from hjudge.commons.db.uow import SQLAlchemyUnitOfWork
from hjudge.commons.errors import UOWSessionNotFoundError


def test_access_to_current_session_without_entering(uow: SQLAlchemyUnitOfWork):
    with pytest.raises(UOWSessionNotFoundError):
        uow.current_session
