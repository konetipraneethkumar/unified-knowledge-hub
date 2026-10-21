from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class KnowledgeItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1)
    source_item_id: str = Field(min_length=1)
    title: str | None = None
    item_type: str | None = None
    mime_type: str | None = None
    file_extension: str | None = None
    file_size_bytes: int | None = None
    file_created_at: datetime | None = None
    location: str | None = None
    parent_location: str | None = None
    web_url: str | None = None
    file_path: str | None = None
    source_metadata: dict[str, Any] | None = None
    summary: str | None = None
    modified_at: datetime | None = None


class KnowledgeItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    connector_id: str | None = None
    source: str
    source_item_id: str
    title: str | None
    item_type: str | None
    mime_type: str | None
    file_extension: str | None
    file_size_bytes: int | None
    file_created_at: datetime | None
    location: str | None
    parent_location: str | None
    web_url: str | None
    file_path: str | None
    source_metadata: dict[str, Any] | None
    summary: str | None
    processing_status: str = "pending"
    processing_error: str | None = None
    created_at: datetime
    modified_at: datetime | None
    indexed_at: datetime

    @field_validator("location", mode="before")
    @classmethod
    def provide_location_fallback(cls, value: str | None) -> str:
        return value if value else "Location unavailable"

    @computed_field
    @property
    def source_type(self) -> str:
        return self.source

    @computed_field
    @property
    def external_id(self) -> str:
        return self.source_item_id

    @computed_field
    @property
    def date(self) -> datetime | None:
        return self.modified_at or self.file_created_at


class KnowledgeItemSearchResponse(BaseModel):
    query: str
    offset: int = Field(ge=0)
    limit: int = Field(ge=1)
    total: int = Field(ge=0)
    items: list[KnowledgeItemRead]


class KnowledgeItemListResponse(BaseModel):
    offset: int = Field(ge=0)
    limit: int = Field(ge=1)
    total: int = Field(ge=0)
    items: list[KnowledgeItemRead]


class HybridKnowledgeItemResult(BaseModel):
    item: KnowledgeItemRead
    relevance_score: float


class HybridKnowledgeItemSearchResponse(BaseModel):
    query: str
    limit: int = Field(ge=1)
    total: int = Field(ge=0)
    items: list[HybridKnowledgeItemResult]