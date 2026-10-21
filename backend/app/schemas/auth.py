from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=256)
    display_name: str | None = Field(default=None, max_length=255)


class LoginRequest(RegisterRequest):
    display_name: str | None = None


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str = Field(min_length=32, max_length=512)


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str | None = Field(default=None, max_length=255)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    display_name: str | None
    avatar_url: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime


class SessionRead(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead
