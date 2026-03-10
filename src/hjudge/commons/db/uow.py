import abc
from typing import Callable, override

from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import TypedReturnsRows

from hjudge.commons.db.repositories import (
    AbstractRepository,
    SQLAlchemyAbstractRepository,
)
from hjudge.commons.errors import UOWSessionNotFoundError
from hjudge.lms.db.repositories.user import (
    AbstractUserRepository,
    SQLAlchemyUserRepository,
)
from hjudge.oj.db.repositories.exercise import (
    AbstractExerciseRepository,
    SQLAlchemyExerciseRepostory,
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

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        raise NotImplementedError


type SQLAlchemyRepositoryDict = dict[
    type[AbstractRepository], type[SQLAlchemyAbstractRepository]
]
type SessionFactoryCallable = Callable[[], Session]
DEFAULT_SQLALCHEMY_REPOSITORY_DICT: SQLAlchemyRepositoryDict = {
    AbstractUserRepository: SQLAlchemyUserRepository,
    AbstractExerciseRepository: SQLAlchemyExerciseRepostory,
    AbstractSubmissionRepository: SQLAlchemySubmissionRepository,
}


class SQLAlchemyUnitOfWork(AbstractUnitOfWork):
    """A UoW class, that is meant to be used once and then dispose"""

    session_factory: SessionFactoryCallable
    _session: Session | None
    repositories_dict: SQLAlchemyRepositoryDict

    def __init__(
        self,
        session_factory: SessionFactoryCallable,
        repositories_dict: SQLAlchemyRepositoryDict = DEFAULT_SQLALCHEMY_REPOSITORY_DICT,
    ):
        self.session_factory = session_factory
        self._session = None
        self.repositories_dict = repositories_dict
        self.used = False

    def __enter__(self):
        self._session = self.session_factory()
        assert self._session is not None
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        # self.session.flush()
        self.session.expunge_all()
        self.session.close()
        self._session = None

    @property
    def session(self) -> Session:
        if self._session is None:
            raise UOWSessionNotFoundError
        return self._session

    def create_repository(
        self, constructor: type[AbstractRepository]
    ) -> SQLAlchemyAbstractRepository:
        constructor = self.repositories_dict[constructor]
        return constructor(session=self.session)

    @override
    def commit(self) -> None:
        self.session.commit()

    @override
    def rollback(self):
        self.session.rollback()

    @override
    def execute(self, statement: TypedReturnsRows, *args, **kwargs):
        self.session.execute(statement)


class AbstractUOWFactory(abc.ABC):
    def create_uow(self) -> AbstractUnitOfWork:
        raise NotImplementedError


class SQLAlchemyUOWFactory(AbstractUOWFactory):
    def __init__(self, session_factory: SessionFactoryCallable) -> None:
        self.session_factory = session_factory

    def create_uow(self) -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(session_factory=self.session_factory)
