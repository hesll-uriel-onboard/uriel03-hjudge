from hjudge.commons.db.uow import AbstractUnitOfWork
from hjudge.oj.db.entities.exercise import ExerciseEntity
from hjudge.oj.db.repositories.exercise import AbstractExerciseRepository
from hjudge.oj.models.judges import Exercise, JudgeEnum
from hjudge.oj.models.judges.factory import JudgeFactory


async def check_exercise_existence(
    judge_name: JudgeEnum,
    exercise_code: str,
    judge_factory: JudgeFactory,
    uow: AbstractUnitOfWork,
) -> Exercise | None:
    with uow:
        # if existed, return immediately
        repository: AbstractExerciseRepository = uow.create_repository(
            AbstractExerciseRepository
        )  # pyright:ignore
        result_entity = repository.get_exercise_by_judge_and_code(
            judge=judge_name, code=exercise_code
        )
        if result_entity is not None:
            result = result_entity.as_model()
            uow.commit()
            return result

        # otherwise, try crawling
        judge = judge_factory.create_from(judge_name)
        config = judge.get_batch_config(from_exercise=exercise_code)

        # Use async context manager for browser lifecycle
        async with judge:
            result_models = await judge.crawl_exercises_batch(**config)
        repository.add_exercises(
            [ExerciseEntity.from_model(model) for model in result_models]
        )

        # recheck once again
        result_entity = repository.get_exercise_by_judge_and_code(
            judge=judge_name, code=exercise_code
        )
        uow.commit()
        return None if result_entity is None else result_entity.as_model()
