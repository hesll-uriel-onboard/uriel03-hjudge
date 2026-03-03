"""init and create User table

Revision ID: 0001
Revises:
Create Date: 2026-03-02 12:19:21.082642

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from hjudge.lms.db.tables.user import user_table

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USER_TABLE = "User"
def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        USER_TABLE,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True, nullable=False),
        sa.Column("username", sa.String, unique=True, nullable=False),
        sa.Column("password", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table(USER_TABLE)
    pass
