from uuid import UUID

from pydantic import BaseModel


class CreateCourseRequest(BaseModel):
    title: str
    content: str
    slug: str


class UpdateCourseRequest(BaseModel):
    title: str
    content: str


class CreateLessonRequest(BaseModel):
    title: str
    content: str
    slug: str
    exercise_ids: list[UUID] = []


class AddAdminRequest(BaseModel):
    user_id: UUID