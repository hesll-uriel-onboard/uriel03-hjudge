from uuid import UUID

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.oj.models.judge import AbstractJudge, Exercise


def check_problem_existed(
    judge: AbstractJudge, exercise_code: str, uow: AbstractUnitOfWork
) -> Exercise:
    raise NotImplementedError


def change_state(
    user: UUID, exercise: Exercise, solved: bool, uow: AbstractUnitOfWork
) -> bool:
    raise NotImplementedError
