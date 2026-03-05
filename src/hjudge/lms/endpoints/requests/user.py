from dataclasses import dataclass

from pydantic import BaseModel


class UserRegisterRequest(BaseModel):
    username: str
    password: str
    name: str


class UserLoginRequest(BaseModel):
    username: str
    password: str
