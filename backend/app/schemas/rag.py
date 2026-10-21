from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RagAnswerRequest(BaseModel):
	query: str = Field(min_length=1, max_length=200)


class TrustedSourceReferenceRead(BaseModel):
	location: str | None
	web_url: str | None
	file_path: str | None
	parent_location: str | None
	metadata: dict[str, Any] | None


class AnswerSourceRead(BaseModel):
	source_id: str
	source_type: str
	title: str | None
	date: datetime | None
	evidence: str
	trusted_source_reference: TrustedSourceReferenceRead


class RagAnswerResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	query: str
	answer: str
	status: str
	sources: list[AnswerSourceRead]
