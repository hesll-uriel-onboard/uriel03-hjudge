import uuid
from typing import Self
from uuid import UUID

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
)

from hjudge.commons.models import entity_dumps


class BaseEntity(DeclarativeBase, MappedAsDataclass, kw_only=True):
    id: Mapped[UUID] = mapped_column(
        primary_key=True, default_factory=lambda: uuid.uuid4()
    )

    def as_model(self):
        raise NotImplementedError

    @classmethod
    def from_model(cls, object) -> Self:
        return cls(**entity_dumps(object))
