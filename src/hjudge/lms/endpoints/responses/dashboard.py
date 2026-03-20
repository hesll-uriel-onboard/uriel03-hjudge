"""Dashboard response classes."""

from typing import override

from hjudge.commons.endpoints.responses import AbstractResponse
from hjudge.commons.endpoints.status_codes import HTTP_200_OK
from hjudge.lms.models.dashboard import Leaderboard, ProgressEntry


class ProgressEntryResponse(AbstractResponse):
    @override
    def __init__(self, entry: ProgressEntry):
        result = entry.model_dump(mode="json")
        super().__init__(status_code=HTTP_200_OK, content=result)


class LeaderboardResponse(AbstractResponse):
    @override
    def __init__(self, leaderboard: Leaderboard):
        result = leaderboard.model_dump(mode="json")
        super().__init__(status_code=HTTP_200_OK, content=result)