import uuid

import pydantic


class Base(pydantic.BaseModel):
    id: uuid.UUID = pydantic.Field(default_factory=lambda: uuid.uuid4())
