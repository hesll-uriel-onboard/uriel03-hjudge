from typing import Protocol, override

from sqlalchemy.orm import Session


class AbstractRepository(Protocol):
    """AbstractRepository"""


class SQLAlchemyAbstractRepository(AbstractRepository):
    session: Session

    @override
    def __init__(self, session) -> None:
        self.session = session
