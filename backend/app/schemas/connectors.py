from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    created_at: datetime
    last_seen_at: datetime | None
    revoked_at: datetime | None


class PairingRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class PairingRead(BaseModel):
    code: str
    expires_at: datetime


class PairingCompleteRequest(BaseModel):
    code: str = Field(min_length=6, max_length=64)
    name: str = Field(min_length=1, max_length=120)


class DeviceCredentialRead(BaseModel):
    device: DeviceRead
    credential: str


class ConnectorCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    connector_type: str = Field(pattern="^(LOCAL|GMAIL|GOOGLE_DRIVE)$")
    name: str = Field(min_length=1, max_length=120)
    device_id: str | None = None
    authorized_root: str | None = None


class ConnectorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    connector_type: str
    provider: str
    name: str
    device_id: str | None
    status: str
    authentication_status: str
    authorized_root: str | None
    created_at: datetime
    last_sync_at: datetime | None
    revoked_at: datetime | None
