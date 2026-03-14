import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import Engine

from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.oj.db.entities.user_judge import UserJudgeEntity
from hjudge.oj.db.repositories.user_judge import AbstractUserJudgeRepository
from hjudge.oj.db.tables import user_judge_table
from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.user_judge import UserJudge

# Sample data
USER_ID_1 = uuid.uuid4()
USER_ID_2 = uuid.uuid4()
DEFAULT_LAST_CRAWLED = datetime.fromtimestamp(0, tz=timezone.utc)
LATER_TIMESTAMP = datetime(2026, 3, 13, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def clear_tables(engine: Engine):
    with engine.connect() as connection:
        connection.execute(user_judge_table.delete())
        connection.commit()


def test_add_user_judge(uow: AbstractUnitOfWork):
    # with
    user_judge = UserJudge(
        user_id=USER_ID_1,
        judge=JudgeEnum.CODEFORCES,
        handle="testuser",
    )

    # act
    with uow:
        repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        repo.upsert(UserJudgeEntity.from_model(user_judge))
        uow.commit()

    # assert
    with uow:
        repo = uow.create_repository(AbstractUserJudgeRepository)  # pyright: ignore
        result = repo.get_by_user_and_judge(USER_ID_1, JudgeEnum.CODEFORCES)
        assert result is not None
        result_model = result.as_model()
        assert result_model.user_id == USER_ID_1
        assert result_model.judge == JudgeEnum.CODEFORCES
        assert result_model.handle == "testuser"
        uow.rollback()


def test_upsert_updates_existing(uow: AbstractUnitOfWork):
    # with - create initial
    user_judge = UserJudge(
        user_id=USER_ID_1,
        judge=JudgeEnum.CODEFORCES,
        handle="testuser",
    )

    with uow:
        repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        repo.upsert(UserJudgeEntity.from_model(user_judge))
        uow.commit()

    # act - upsert with new handle
    updated_user_judge = UserJudge(
        user_id=USER_ID_1,
        judge=JudgeEnum.CODEFORCES,
        handle="newhandle",
    )

    with uow:
        repo = uow.create_repository(AbstractUserJudgeRepository)  # pyright: ignore
        repo.upsert(UserJudgeEntity.from_model(updated_user_judge))
        uow.commit()

    # assert - handle should be updated
    with uow:
        repo = uow.create_repository(AbstractUserJudgeRepository)  # pyright: ignore
        result = repo.get_by_user_and_judge(USER_ID_1, JudgeEnum.CODEFORCES)
        assert result is not None
        result_model = result.as_model()
        uow.rollback()

    assert result_model.handle == "newhandle"


def test_list_by_user(uow: AbstractUnitOfWork):
    # with - create multiple handles for one user
    user_judge_1 = UserJudge(
        user_id=USER_ID_1,
        judge=JudgeEnum.CODEFORCES,
        handle="cf_handle",
    )
    # Note: Adding more judges would require expanding JudgeEnum
    # For now, test with single judge per user

    with uow:
        repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        repo.upsert(UserJudgeEntity.from_model(user_judge_1))
        uow.commit()

    # act
    with uow:
        repo = uow.create_repository(AbstractUserJudgeRepository)  # pyright: ignore
        result = repo.list_by_user(USER_ID_1)
        models = [e.as_model() for e in result]
        uow.rollback()

    # assert
    assert len(models) == 1
    assert models[0].handle == "cf_handle"


def test_list_all(uow: AbstractUnitOfWork):
    # with - create handles for multiple users
    user_judge_1 = UserJudge(
        user_id=USER_ID_1,
        judge=JudgeEnum.CODEFORCES,
        handle="user1_handle",
    )
    user_judge_2 = UserJudge(
        user_id=USER_ID_2,
        judge=JudgeEnum.CODEFORCES,
        handle="user2_handle",
    )

    with uow:
        repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        repo.upsert(UserJudgeEntity.from_model(user_judge_1))
        repo.upsert(UserJudgeEntity.from_model(user_judge_2))
        uow.commit()

    # act
    with uow:
        repo = uow.create_repository(AbstractUserJudgeRepository)  # pyright: ignore
        result = repo.list_all()
        models = [e.as_model() for e in result]
        uow.rollback()

    # assert
    assert len(models) == 2


def test_update_last_crawled(uow: AbstractUnitOfWork):
    # with - create initial
    user_judge = UserJudge(
        user_id=USER_ID_1,
        judge=JudgeEnum.CODEFORCES,
        handle="testuser",
    )

    with uow:
        repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        repo.upsert(UserJudgeEntity.from_model(user_judge))
        uow.commit()

    # get the entity id
    with uow:
        repo = uow.create_repository(AbstractUserJudgeRepository)  # pyright: ignore
        entity = repo.get_by_user_and_judge(USER_ID_1, JudgeEnum.CODEFORCES)
        assert entity is not None
        entity_id = entity.id
        uow.rollback()

    # act - update last_crawled
    with uow:
        repo = uow.create_repository(AbstractUserJudgeRepository)  # pyright: ignore
        repo.update_last_crawled(entity_id, LATER_TIMESTAMP)
        uow.commit()

    # assert
    with uow:
        repo = uow.create_repository(AbstractUserJudgeRepository)  # pyright: ignore
        result = repo.get_by_user_and_judge(USER_ID_1, JudgeEnum.CODEFORCES)
        assert result is not None
        result_model = result.as_model()
        uow.rollback()

    assert result_model.last_crawled.replace(tzinfo=None) == LATER_TIMESTAMP.replace(tzinfo=None)


def test_unique_constraint_user_judge(uow: AbstractUnitOfWork):
    """Test that user_id + judge must be unique"""
    user_judge_1 = UserJudge(
        user_id=USER_ID_1,
        judge=JudgeEnum.CODEFORCES,
        handle="handle1",
    )

    with uow:
        repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        repo.upsert(UserJudgeEntity.from_model(user_judge_1))
        uow.commit()

    # Try to add another with same user_id + judge (should update, not create new)
    user_judge_2 = UserJudge(
        user_id=USER_ID_1,
        judge=JudgeEnum.CODEFORCES,
        handle="handle2",
    )

    with uow:
        repo = uow.create_repository(AbstractUserJudgeRepository)  # pyright: ignore
        repo.upsert(UserJudgeEntity.from_model(user_judge_2))
        uow.commit()

    # Should still only have one entry
    with uow:
        repo = uow.create_repository(AbstractUserJudgeRepository)  # pyright: ignore
        result = repo.list_all()
        models = [e.as_model() for e in result]
        uow.rollback()

    assert len(models) == 1
    assert models[0].handle == "handle2"