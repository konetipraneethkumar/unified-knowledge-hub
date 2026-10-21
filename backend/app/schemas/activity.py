from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SearchHistoryCreate(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    mode: Literal["ask", "search"] = "ask"
    result_count: int = Field(ge=0)
    source_count: int = Field(ge=0)


class SearchHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    mode: Literal["ask", "search"]
    result_count: int
    source_count: int
    created_at: datetime


class ConnectorSyncActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    connector_id: str | None
    connector_name: str
    connector_type: str
    status: str
    processed: int | None
    skipped: int | None
    failed: int | None
    deleted: int | None
    created_at: datetime
