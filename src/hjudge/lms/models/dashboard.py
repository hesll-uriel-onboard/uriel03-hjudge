"""Dashboard models for progress tracking and leaderboards."""

from uuid import UUID

from hjudge.commons.models import Base
from hjudge.lms.models.user import User


class ProgressEntry(Base):
    """A user's progress with breakdown by exercise or lesson."""

    user: User
    total_points: float  # scaled 0-100
    breakdown: dict[UUID, float]  # exercise_id or lesson_id -> points (0-100)


class Leaderboard(Base):
    """Leaderboard with sorted entries."""

    entries: list[ProgressEntry]