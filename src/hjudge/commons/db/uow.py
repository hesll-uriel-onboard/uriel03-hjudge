import abc
from typing import override

from sqlalchemy import Engine
from sqlalchemy.orm import Session, create_session

from hjudge.commons.db import AbstractRepository, SQLAlchemyAbstractRepository
from hjudge.commons.errors import UOWSessionNotFoundError
from hjudge.lms.db.repositories.user import (
    AbstractUserRepository,
    SQLAlchemyUserRepository,
)
from hjudge.oj.db.repositories.judge import (
    AbstractExerciseRepository,
    SQLAlchemyExerciseRepository,
)
from hjudge.oj.db.repositories.submission import (
    AbstractSubmissionRepository,
    SQLAlchemySubmissionRepository,
)


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


SQLAlchemyRepositoryDict = dict[
    type[AbstractRepository], type[SQLAlchemyAbstractRepository]
]
DEFAULT_SQLALCHEMY_REPOSITORY_DICT: SQLAlchemyRepositoryDict = {
    AbstractUserRepository: SQLAlchemyUserRepository,
    AbstractExerciseRepository: SQLAlchemyExerciseRepository,
    AbstractSubmissionRepository: SQLAlchemySubmissionRepository,
}


class SQLAlchemyUnitOfWork(AbstractUnitOfWork):

    engine: Engine
    _current_session: Session | None
    repositories_dict: SQLAlchemyRepositoryDict

    def __init__(
        self,
        engine: Engine,
        repositories_dict: SQLAlchemyRepositoryDict = DEFAULT_SQLALCHEMY_REPOSITORY_DICT,
    ):
        self.engine = engine
        self._current_session = None
        self.repositories_dict = repositories_dict

    def __enter__(self):
        self._current_session = create_session(self.engine)
        assert self._current_session is not None
        return super().__enter__()

    def __exit__(self, *args):
        self.current_session.expunge_all()
        self.current_session.close()
        return super().__exit__(*args)

    @property
    def current_session(self) -> Session:
        if self._current_session is None:
            raise UOWSessionNotFoundError
        return self._current_session

    def create_repository(
        self, constructor: type[AbstractRepository]
    ) -> SQLAlchemyAbstractRepository:
        constructor = self.repositories_dict[constructor]
        return constructor(session=self.current_session)

    @override
    def commit(self) -> None:
        self.current_session.commit()

    @override
    def rollback(self):
        self.current_session.rollback()
        self._current_session = None
