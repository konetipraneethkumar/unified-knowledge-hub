from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1)
    source_item_id: str = Field(min_length=1)
    title: str | None = None
    item_type: str | None = None
    mime_type: str | None = None
    location: str | None = None
    summary: str | None = None
    modified_at: datetime | None = None


class KnowledgeItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    source_item_id: str
    title: str | None
    item_type: str | None
    mime_type: str | None
    location: str | None
    summary: str | None
    created_at: datetime
    modified_at: datetime | None
    indexed_at: datetime