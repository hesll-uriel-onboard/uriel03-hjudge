import uuid
from uuid import UUID

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
)


class Base(DeclarativeBase, MappedAsDataclass, kw_only=True):
    id: Mapped[UUID] = mapped_column(
        primary_key=True, default_factory=lambda: uuid.uuid4()
    )
