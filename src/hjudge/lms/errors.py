############## User ##############
class UserExistedError(Exception):
    """User existed"""


class UserNotFoundError(Exception):
    """User not found"""


class UserWrongPasswordError(Exception):
    """Login with wrong credential"""


class CookieExistedError(Exception):
    """Cookie existed"""
