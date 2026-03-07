import sqlalchemy as sa

from hjudge.commons.db import mapper_registry
from hjudge.oj.models.judges import JudgeEnum
from hjudge.oj.models.submission import Verdict

exercise_table = sa.Table(
    "Exercise",
    mapper_registry.metadata,
    sa.Column("id", sa.Uuid, primary_key=True, nullable=False),
    sa.Column("judge", sa.Enum(JudgeEnum), nullable=False),
    sa.Column("code", sa.String, nullable=False),
    sa.Column("title", sa.String, nullable=False),
    sa.UniqueConstraint("judge", "code"),
)
submission_table = sa.Table(
    "Submission",
    mapper_registry.metadata,
    sa.Column("id", sa.Uuid, primary_key=True),
    sa.Column(
        "exercise_id",
        sa.Uuid,
        sa.ForeignKey("Exercise.id", name="fk_exercise_id"),
    ),
    sa.Column("user_id", sa.Uuid, nullable=False),
    sa.Column("submitted_at", sa.DateTime, nullable=False),
    sa.Column("verdict", sa.Enum(Verdict), nullable=False),
)
# user_judge_table = sa.Table(
#     "UserJudge",
#     mapper_registry.metadata,
#     sa.Column("id", sa.Uuid, primary_key=True, nullable=False),
#     sa.Column("user_id", sa.Uuid),
#     sa.Column("judge", sa.Enum(JudgeEnum), nullable=False),
#     sa.Column("handle", sa.String, nullable=False, default=True),
# )
