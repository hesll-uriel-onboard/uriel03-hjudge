"""add user_judge table and extend submission

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USER_JUDGE_TABLE = "UserJudge"
SUBMISSION_TABLE = "Submission"


def upgrade() -> None:
    """Upgrade schema."""
    # Add submission_id and content columns to Submission
    op.add_column(
        SUBMISSION_TABLE,
        sa.Column("submission_id", sa.String, nullable=True),
    )
    op.add_column(
        SUBMISSION_TABLE,
        sa.Column("content", sa.String, nullable=False, server_default=""),
    )

    # Create UserJudge table - reuse existing judgeenum type from migration 0003
    op.create_table(
        USER_JUDGE_TABLE,
        sa.Column("id", sa.Uuid, primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid, nullable=False),
        sa.Column("judge", sa.String, nullable=False),
        sa.Column("handle", sa.String, nullable=False),
        sa.Column(
            "last_crawled",
            sa.DateTime,
            nullable=False,
            server_default="1970-01-01 00:00:00",
        ),
        sa.UniqueConstraint("user_id", "judge", name="uq_user_judge"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table(USER_JUDGE_TABLE)
    op.drop_column(SUBMISSION_TABLE, "content")
    op.drop_column(SUBMISSION_TABLE, "submission_id")
