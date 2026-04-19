"""add LQDOJ judge enum

Revision ID: 0008
Revises: 0007
Create Date: 2026-03-29

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, Sequence[str], None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add LQDOJ enum value."""
    # Get the database dialect
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # Add LQDOJ to judgeenum
        op.execute("ALTER TYPE judgeenum ADD VALUE IF NOT EXISTS 'LQDOJ'")
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