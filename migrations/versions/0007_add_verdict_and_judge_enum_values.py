"""add CE, IE verdicts and DMOJ, ATCODER, QOJ judge enums

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-21

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, Sequence[str], None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add new enum values."""
    # Get the database dialect
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # Add CE and IE to Verdict enum
        op.execute("ALTER TYPE verdict ADD VALUE IF NOT EXISTS 'CE'")
        op.execute("ALTER TYPE verdict ADD VALUE IF NOT EXISTS 'IE'")

        # Add DMOJ and QOJ to judgeenum
        # Note: ATCODER already exists from migration 0003
        # Note: VNOJ exists in DB but was removed from Python code (kept for backward compatibility)
        op.execute("ALTER TYPE judgeenum ADD VALUE IF NOT EXISTS 'DMOJ'")
        op.execute("ALTER TYPE judgeenum ADD VALUE IF NOT EXISTS 'QOJ'")
    # For SQLite and other databases, enum values are handled by SQLAlchemy
    # based on the Python enum definition, so no migration needed.


def downgrade() -> None:
    """Downgrade schema.

    Note: PostgreSQL does not support removing enum values directly.
    You would need to drop and recreate the enum type, which requires
    dropping all columns that use it first.
    """
    # Cannot easily remove enum values in PostgreSQL
    # This is a limitation of PostgreSQL enum types
    pass