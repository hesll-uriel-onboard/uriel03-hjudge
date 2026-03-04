"""create UserSession table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-02 12:21:25.172068

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USER_SESSION_TABLE = "UserSession"


def upgrade() -> None:
    op.create_table(
        USER_SESSION_TABLE,
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "user_id", sa.Uuid, sa.ForeignKey("User.id", name="fk_user_id")
        ),
        sa.Column("cookie", sa.String, nullable=False, unique=True),
        sa.Column("issued_at", sa.DateTime, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, default=True),
    )
    pass


def downgrade() -> None:
    op.drop_table(USER_SESSION_TABLE)
    pass
