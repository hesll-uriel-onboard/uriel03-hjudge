"""create Exercise and Submission tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-07 01:02:12.366938

"""

from enum import Enum
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXERCISE_TABLE_NAME = "Exercise"
SUBMISSION_TABLE_NAME = "Submission"


class JudgeEnum(Enum):
    CODEFORCES = "Codeforces"
    ATCODER = "AtCoder"
    VNOJ = "VNOJ"


class Verdict(Enum):
    AC = "Accepted"
    WA = "Wrong Answer"
    TLE = "Time Limit Exceeded"
    RTE = "Run-Time Error"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        EXERCISE_TABLE_NAME,
        sa.Column("id", sa.Uuid, primary_key=True, nullable=False),
        sa.Column("judge", sa.Enum(JudgeEnum), nullable=False),
        sa.Column("code", sa.String, nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.UniqueConstraint("judge", "code"),
    )
    op.create_table(
        SUBMISSION_TABLE_NAME,
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "exercise_id",
            sa.Uuid,
            sa.ForeignKey("Exercise.id", name="fk_exercise_id"),
        ),
        sa.Column("user_id", sa.Uuid, nullable=False),
        sa.Column("verdict", sa.Enum(Verdict), nullable=False),
        sa.Column("submitted_at", sa.DateTime, nullable=False),
    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table(SUBMISSION_TABLE_NAME)
    op.drop_table(EXERCISE_TABLE_NAME)
    sa.Enum(JudgeEnum).drop(op.get_bind())
    sa.Enum(Verdict).drop(op.get_bind())
    pass
