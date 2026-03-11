"""add course lesson and course_admin tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-11 18:59:43.597660

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COURSE = "Course"
COURSE_ADMIN = "CourseAdmin"
LESSON = "Lesson"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        COURSE,
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("content", sa.String, nullable=False),
        sa.Column("slug", sa.String, nullable=False, unique=True),
    )
    op.create_table(
        "Lesson",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("content", sa.String, nullable=False),
        sa.Column("slug", sa.String, nullable=False),
        sa.Column(
            "course_id",
            sa.Uuid,
            sa.ForeignKey("Course.id", name="fk_lesson_course_id"),
        ),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("exercise_ids", sa.JSON),
        sa.UniqueConstraint("course_id", "slug"),
    )
    op.create_table(
        COURSE_ADMIN,
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "course_id",
            sa.Uuid,
            sa.ForeignKey("Course.id", name="fk_admin_course_id"),
        ),
        sa.Column(
            "user_id",
            sa.Uuid,
            sa.ForeignKey("User.id", name="fk_admin_user_id"),
        ),
        sa.UniqueConstraint("course_id", "user_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table(COURSE_ADMIN)
    op.drop_table(LESSON)
    op.drop_table(COURSE)
