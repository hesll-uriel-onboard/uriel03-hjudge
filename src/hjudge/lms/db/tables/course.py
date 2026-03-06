import sqlalchemy as sa

from hjudge.commons.db import mapper_registry

course_table = sa.Table(
    "Course",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID, primary_key=True, nullable=False),
    sa.Column("title", sa.String, nullable=False),
    sa.Column("content", sa.String, nullable=False),
)

lesson_table = sa.Table(
    "Course",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID, primary_key=True, nullable=False),
    sa.Column("title", sa.String, nullable=False),
    sa.Column("content", sa.String, nullable=False),
)
