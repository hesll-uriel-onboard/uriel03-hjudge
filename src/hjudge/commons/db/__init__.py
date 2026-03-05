from typing import Protocol, override

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, registry

mapper_registry = registry()
DEFAULT_CONNECTION_STRING = "postgresql://postgres:example@localhost/hjudge"
DEFAULT_ENGINE = create_engine(DEFAULT_CONNECTION_STRING)


class AbstractRepository(Protocol):
    """AbstractRepository"""


class SQLAlchemyAbstractRepository(AbstractRepository):
    session: Session

    @override
    def __init__(self, session, **kwargs) -> None:
        self.session = session
