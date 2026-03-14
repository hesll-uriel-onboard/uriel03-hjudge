from uuid import UUID

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.oj.db.entities.user_judge import UserJudgeEntity
from hjudge.oj.db.repositories.user_judge import AbstractUserJudgeRepository
from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.user_judge import UserJudge


def update_user_judges(
    user_id: UUID, judges: list[tuple[JudgeEnum, str]], uow: AbstractUnitOfWork
) -> list[UserJudge]:
    """Upsert user's judge handles.

    Args:
        user_id: The user's ID
        judges: List of (judge, handle) tuples
        uow: Unit of work

    Returns:
        List of updated UserJudge objects
    """
    with uow:
        repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore

        result = []
        for judge, handle in judges:
            user_judge = UserJudge(user_id=user_id, judge=judge, handle=handle)
            repo.upsert(UserJudgeEntity.from_model(user_judge))
            result.append(user_judge)

        uow.commit()
        return result


def get_user_judges(user_id: UUID, uow: AbstractUnitOfWork) -> list[UserJudge]:
    """Get all judge handles for a user.

    Args:
        user_id: The user's ID
        uow: Unit of work

    Returns:
        List of UserJudge objects
    """
    with uow:
        repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        entities = repo.list_by_user(user_id)
        models = [e.as_model() for e in entities]
        uow.rollback()
        return models