from litestar import MediaType, get
from litestar.response import Template

from hjudge.commons.db.uow import AbstractUOWFactory
from hjudge.commons.endpoints.responses import ErrorResponse
from hjudge.commons.errors import AbstractError
from hjudge.lms.endpoints.authentication import authenticate_user
from hjudge.lms.endpoints.responses.user import COOKIE_KEY
from hjudge.oj.db.repositories.exercise import AbstractExerciseRepository
from hjudge.oj.db.repositories.submission import AbstractSubmissionRepository
from hjudge.oj.errors import ExerciseNotFoundError
from hjudge.oj.models.judges.factory import JudgeFactory

PER_PAGE = 20


@get("/exercises", media_type=MediaType.HTML, include_in_schema=False)
async def get_exercises(
    cookies: dict[str, str],
    uow_factory: AbstractUOWFactory,
    judge_factory: JudgeFactory,
    page: int = 1,
) -> Template | ErrorResponse:
    cookie: str | None = cookies.get(COOKIE_KEY)
    user = authenticate_user(cookie, uow_factory.create_uow(), required=False)
    # TODO: put this in a service
    try:
        with uow_factory.create_uow() as uow:
            repo: AbstractExerciseRepository = uow.create_repository(
                AbstractExerciseRepository
            )  # pyright: ignore
            entities, total = repo.get_exercises(page=page, per_page=PER_PAGE)
            exercises = [entity.as_model() for entity in entities]
            exercise_list = [
                {
                    "content": exercise,
                    "url": judge_factory.create_from(
                        exercise.judge
                    ).get_exercise_url(exercise.code),
                }
                for exercise in exercises
            ]

            # Fetch progress for logged-in users
            progress: dict[str, dict[str, int | bool]] = {}
            if user is not None:
                exercise_ids = [e.id for e in exercises]
                sub_repo: AbstractSubmissionRepository = uow.create_repository(
                    AbstractSubmissionRepository
                )  # pyright: ignore
                max_points_map = sub_repo.get_max_points_by_exercise_and_user(
                    exercise_ids, [user.id]
                )

                # Also check for AC verdicts
                from sqlalchemy import and_, func, or_

                from hjudge.oj.db.entities.submission import SubmissionEntity

                ac_exercises = (
                    uow.session.query(SubmissionEntity.exercise_id)
                    .filter(
                        SubmissionEntity.exercise_id.in_(exercise_ids),
                        SubmissionEntity.user_id == user.id,
                        SubmissionEntity.verdict == "AC",
                    )
                    .distinct()
                    .all()
                )
                ac_set = {row[0] for row in ac_exercises}

                for exercise in exercises:
                    max_points = max_points_map.get((exercise.id, user.id), 0)
                    progress[str(exercise.id)] = {
                        "max_points": max_points,
                        "has_ac": exercise.id in ac_set,
                    }

            uow.rollback()

        total_pages = (total + PER_PAGE - 1) // PER_PAGE

        return Template(
            template_name="views/exercises.jinja",
            context={
                "exercises": exercise_list,
                "user": user,
                "progress": progress,
                "page": page,
                "total_pages": total_pages,
                "total": total,
            },
        )
    except AbstractError as e:
        return ErrorResponse(e)


lms_frontends = [get_exercises]
