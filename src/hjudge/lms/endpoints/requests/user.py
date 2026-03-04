from dataclasses import dataclass


@dataclass
class UserRegisterRequest:
    username: str
    password: str
    name: str


@dataclass
class UserLoginRequest:
    username: str
    password: str
