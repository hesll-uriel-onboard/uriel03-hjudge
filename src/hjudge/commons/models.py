import uuid
from typing import Any

import pydantic


class Base(pydantic.BaseModel):
    id: uuid.UUID = pydantic.Field(default_factory=lambda: uuid.uuid4())


def entity_dumps(obj) -> dict[str, Any]:
    result: dict[str, Any] = dict()
    for key, value in type(obj).model_fields.items():
        if issubclass(value.annotation, Base):
            new_k = f"{key}_id"
            new_v = getattr(obj, key).id
        else:
            new_k = key
            new_v = getattr(obj, key)
        print(new_k, new_v)
        result[new_k] = new_v
    return result
