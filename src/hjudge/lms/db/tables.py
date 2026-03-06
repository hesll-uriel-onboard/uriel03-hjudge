import sqlalchemy as sa

from hjudge.commons.db import mapper_registry

user_table = sa.Table(
    "User",
    mapper_registry.metadata,
    sa.Column("id", sa.Uuid, primary_key=True, nullable=False),
    sa.Column("username", sa.String, unique=True, nullable=False),
    sa.Column("password", sa.String, nullable=False),
    sa.Column("name", sa.String, nullable=False),
)
user_session_table = sa.Table(
    "UserSession",
    mapper_registry.metadata,
    sa.Column("id", sa.Uuid, primary_key=True),
    sa.Column("user_id", sa.Uuid, sa.ForeignKey("User.id", name="fk_user_id")),
    sa.Column("cookie", sa.String, nullable=False, unique=True),
    sa.Column("issued_at", sa.DateTime, nullable=False),
    sa.Column("active", sa.Boolean, nullable=False, default=True),
)
