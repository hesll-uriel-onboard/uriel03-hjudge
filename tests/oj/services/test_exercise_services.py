from typing import Any, List
from uuid import UUID

import pytest
from typing_extensions import override

from hjudge.commons.db.repositories import AbstractRepository
from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.oj.db.entities.exercise import ExerciseEntity
from hjudge.oj.db.repositories.exercise import AbstractExerciseRepository
from hjudge.oj.models.judges import (
    AbstractJudge,
    DefaultCrawler,
    Exercise,
    JudgeEnum,
)
from hjudge.oj.services import exercise as services

exercises_list = [
    Exercise(judge=JudgeEnum.CODEFORCES, code=prob, title=prob)
    for prob in ["abc", "def", "ghi"]
]


class FakeJudge(AbstractJudge):
    @override
    def get_batch_config(self, from_exercise: str) -> dict[str, Any]:
        return {}

    @override
    def get_exercise_url(self, id: str) -> str:
        return f"{id}"

    @override
    def crawl_exercises_batch(self, url: str, **kwargs) -> List[Exercise]:
        return exercises_list


class FakeRepo(AbstractExerciseRepository):
    __exercises: dict[UUID, ExerciseEntity] = {}

    def __init__(self) -> None:
        super().__init__()

    @override
    def add_exercise(self, exercise: ExerciseEntity):
        self.__exercises[exercise.id] = exercise

    @override
    def get_exercise(self, id: UUID) -> ExerciseEntity | None:
        return self.__exercises.get(id)

    @override
    def add_exercises(self, exercises: List[ExerciseEntity]):
        for exercise in exercises:
            self.add_exercise(exercise)

    @override
    def get_exercise_by_judge_and_code(
        self, judge: JudgeEnum, code: str
    ) -> ExerciseEntity | None:
        for exercise in self.__exercises.values():
            if exercise.judge == judge and exercise.code == code:
                return exercise
        return None


class FakeUoW(AbstractUnitOfWork):
    repo: FakeRepo = FakeRepo()
    committed = False

    def __init__(self) -> None:
        super().__init__()

    @override
    def __enter__(self):
        self.commited = False
        return super().__enter__()

    @override
    def create_repository(self, constructor) -> AbstractRepository:
        return FakeRepo()

    @override
    def commit(self):
        self.committed = True

    @override
    def rollback(self):
        self.committed = False


@pytest.fixture()
def fake_uow() -> FakeUoW:
    return FakeUoW()


@pytest.mark.parametrize(
    ["uow", "judge"], [(FakeUoW(), FakeJudge(DefaultCrawler()))]
)
def test_check_exercise_already_existed(
    uow: AbstractUnitOfWork, judge: AbstractJudge
):
    # with existed problems
    with uow:
        repo: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright: ignore
        entities = [
            ExerciseEntity.from_model(model)
            for model in judge.crawl_exercises_batch(url="123")
        ]
        repo.add_exercises(entities)
        uow.commit()
        pass
    # and
    existed = exercises_list[0]
    # act
    result = services.check_exercise_existence(existed.judge, existed.code, uow)
    # assert
    assert result == existed


@pytest.mark.parametrize(
    ["uow", "judge"], [(FakeUoW(), FakeJudge(DefaultCrawler()))]
)
def test_check_exercise_crawl_to_exist(
    uow: AbstractUnitOfWork, judge: AbstractJudge
):
    # with
    existed = exercises_list[0]
    # act
    result = services.check_exercise_existence(existed.judge, existed.code, uow)
    # assert
    assert result == existed
