"""add points to submission

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, Sequence[str], None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SUBMISSION_TABLE = "Submission"


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        SUBMISSION_TABLE,
        sa.Column("points", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column(SUBMISSION_TABLE, "points")