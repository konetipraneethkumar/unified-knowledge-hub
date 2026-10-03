from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=256)


class LoginRequest(RegisterRequest):
    pass


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    created_at: datetime


class SessionRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
