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
from hjudge.oj.services import user_judge as user_judge_service

USER_ID = uuid.uuid4()


@pytest.fixture(autouse=True)
def clear_user_judge_table(engine: Engine):
    """Clear user_judge table before each test"""
    with engine.connect() as connection:
        connection.execute(user_judge_table.delete())
        connection.commit()


def test_update_user_judges_creates_new(uow: AbstractUnitOfWork):
    # with - no existing handles
    judges = [
        (JudgeEnum.CODEFORCES, "testhandle"),
    ]

    # act
    user_judge_service.update_user_judges(USER_ID, judges, uow)

    # assert
    with uow:
        repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        result = repo.get_by_user_and_judge(USER_ID, JudgeEnum.CODEFORCES)
        assert result is not None
        assert result.handle == "testhandle"
        uow.rollback()


def test_update_user_judges_updates_existing(uow: AbstractUnitOfWork):
    # with - create existing handle
    with uow:
        repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        existing = UserJudge(
            user_id=USER_ID,
            judge=JudgeEnum.CODEFORCES,
            handle="oldhandle",
        )
        repo.upsert(UserJudgeEntity.from_model(existing))
        uow.commit()

    # act - update with new handle
    judges = [
        (JudgeEnum.CODEFORCES, "newhandle"),
    ]
    user_judge_service.update_user_judges(USER_ID, judges, uow)

    # assert
    with uow:
        repo = uow.create_repository(AbstractUserJudgeRepository)  # pyright: ignore
        result = repo.get_by_user_and_judge(USER_ID, JudgeEnum.CODEFORCES)
        assert result is not None
        assert result.handle == "newhandle"
        uow.rollback()


def test_update_user_judges_empty_list_is_noop(uow: AbstractUnitOfWork):
    """Empty list should not remove existing handles"""
    # with - create existing handles
    with uow:
        repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        existing = UserJudge(
            user_id=USER_ID,
            judge=JudgeEnum.CODEFORCES,
            handle="testhandle",
        )
        repo.upsert(UserJudgeEntity.from_model(existing))
        uow.commit()

    # act - pass empty list
    user_judge_service.update_user_judges(USER_ID, [], uow)

    # assert - should still exist
    with uow:
        repo = uow.create_repository(AbstractUserJudgeRepository)  # pyright: ignore
        result = repo.list_by_user(USER_ID)
        assert len(result) == 1
        assert result[0].handle == "testhandle"
        uow.rollback()


def test_update_user_judges_preserves_last_crawled(uow: AbstractUnitOfWork):
    """When updating handle, last_crawled should not be reset"""
    later_time = datetime(2026, 3, 13, 12, 0, 0, tzinfo=timezone.utc)

    # with - create existing with last_crawled
    with uow:
        repo: AbstractUserJudgeRepository = uow.create_repository(
            AbstractUserJudgeRepository
        )  # pyright: ignore
        existing = UserJudge(
            user_id=USER_ID,
            judge=JudgeEnum.CODEFORCES,
            handle="oldhandle",
            last_crawled=later_time,
        )
        repo.upsert(UserJudgeEntity.from_model(existing))
        uow.commit()

    # act - update handle
    judges = [
        (JudgeEnum.CODEFORCES, "newhandle"),
    ]
    user_judge_service.update_user_judges(USER_ID, judges, uow)

    # assert - last_crawled should be preserved
    with uow:
        repo = uow.create_repository(AbstractUserJudgeRepository)  # pyright: ignore
        result = repo.get_by_user_and_judge(USER_ID, JudgeEnum.CODEFORCES)
        assert result is not None
        assert result.handle == "newhandle"
        # SQLite stores without timezone, compare naive datetimes
        assert result.last_crawled.replace(tzinfo=None) == later_time.replace(tzinfo=None)
        uow.rollback()