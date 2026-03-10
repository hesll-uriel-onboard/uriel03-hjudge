from litestar import MediaType, get
from litestar.response import Template

from hjudge.commons.db.uow import AbstractUOWFactory
from hjudge.commons.endpoints.responses import ErrorResponse
from hjudge.commons.errors import AbstractError
from hjudge.lms.endpoints.authentication import authenticate_user
from hjudge.lms.endpoints.responses.user import COOKIE_KEY
from hjudge.oj.db.repositories.exercise import AbstractExerciseRepository
from hjudge.oj.errors import ExerciseNotFoundError
from hjudge.oj.models.judges.factory import JudgeFactory


@get("/exercises", media_type=MediaType.HTML, include_in_schema=False)
async def get_exercises(
    cookies: dict[str, str],
    uow_factory: AbstractUOWFactory,
    judge_factory: JudgeFactory,
) -> Template | ErrorResponse:
    cookie: str | None = cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow())
    # TODO: put this in a service
    try:
        with uow_factory.create_uow() as uow:
            repo: AbstractExerciseRepository = uow.create_repository(
                AbstractExerciseRepository
            )  # pyright: ignore
            result = repo.get_all_exercises()
            if result is None:
                raise ExerciseNotFoundError
            exercises = [entity.as_model() for entity in result]
            result = [
                {
                    "content": exercise,
                    "url": judge_factory.create_from(
                        exercise.judge
                    ).get_exercise_url(exercise.code),
                }
                for exercise in exercises
            ]
            uow.rollback()

        return Template(
            template_name="views/exercises.jinja",
            context={"exercises": result, "user": user},
        )
    except AbstractError as e:
        return ErrorResponse(e)


lms_frontends = [get_exercises]
