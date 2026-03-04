import abc
from typing import override

from sqlalchemy import Engine
from sqlalchemy.orm import Session, create_session

from hjudge.lms.db.repositories import AbstractRepository
from hjudge.lms.db.repositories.user import (
    AbstractUserRepository,
    SQLAlchemyUserRepository,
)
from hjudge.lms.errors import UOWSessionNotFoundError


class AbstractUnitOfWork(abc.ABC):

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def create_repository(self, constructor) -> AbstractRepository:
        raise NotImplementedError

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


class SQLAlchemyUnitOfWork(AbstractUnitOfWork):

    engine: Engine
    _current_session: Session | None
    repositories_dict = {AbstractUserRepository: SQLAlchemyUserRepository}

    def __init__(self, engine: Engine):
        self.engine = engine
        self._current_session = None

    def __enter__(self):
        print("entered")
        self._current_session = create_session(self.engine)
        assert self._current_session is not None
        return super().__enter__()

    def __exit__(self, *args):
        self.current_session.expunge_all()
        return super().__exit__(*args)

    @property
    def current_session(self) -> Session:
        if self._current_session is None:
            raise UOWSessionNotFoundError
        return self._current_session

    def create_repository(self, constructor) -> AbstractRepository:
        constructor = self.repositories_dict[constructor]
        return constructor(self.current_session)

    @override
    def commit(self) -> None:
        self.current_session.commit()

    @override
    def rollback(self):
        self.current_session.rollback()
        self._current_session = None
