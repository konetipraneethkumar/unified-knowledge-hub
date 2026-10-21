"""Build bounded, deterministic answer context from hybrid retrieval results."""
from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any

from app.retrieval.hybrid import RankedKnowledgeItem

_MAX_SOURCE_CONTENT_CHARS = 4_000
_MAX_TOTAL_CONTENT_CHARS = 16_000
_TRUNCATION_MARKER = "\n[Evidence truncated]"


@dataclass(frozen=True)
class TrustedSourceReference:
	"""Application-controlled source locators, kept out of the LLM prompt."""

	location: str | None
	web_url: str | None
	file_path: str | None
	parent_location: str | None
	metadata: dict[str, Any] | None


@dataclass(frozen=True)
class ContextEvidence:
	source_id: str
	source_type: str
	title: str | None
	date: datetime | None
	evidence: str
	trusted_source_reference: TrustedSourceReference
	truncated: bool


@dataclass(frozen=True)
class RagContext:
	query: str
	sources: tuple[ContextEvidence, ...]

	def to_llm_context(self) -> str:
		"""Render only query-relevant evidence, never application source locators."""
		payload = {
			"query": self.query,
			"instructions": (
				"Answer using only the evidence below. Do not generate or guess "
				"source IDs, URLs, filesystem paths, or source locations; the "
				"application attaches source references separately."
			),
			"evidence": [
				{
					"source_type": source.source_type,
					"title": source.title,
					"date": source.date.isoformat() if source.date else None,
					"content": source.evidence,
				}
				for source in self.sources
			],
		}
		return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class RagContextBuilder:
	"""Convert hybrid-ranked KnowledgeItems into bounded answer context."""

	def __init__(
		self,
		*,
		max_source_content_chars: int = _MAX_SOURCE_CONTENT_CHARS,
		max_total_content_chars: int = _MAX_TOTAL_CONTENT_CHARS,
	) -> None:
		if max_source_content_chars < 1:
			raise ValueError("max_source_content_chars must be positive")
		if max_total_content_chars < 1:
			raise ValueError("max_total_content_chars must be positive")
		self.max_source_content_chars = max_source_content_chars
		self.max_total_content_chars = max_total_content_chars

	def build(
		self, query: str, results: list[RankedKnowledgeItem]
	) -> RagContext:
		"""Preserve result order while bounding evidence included in the prompt."""
		if not results:
			return RagContext(query=query, sources=())

		source_budget = min(
			self.max_source_content_chars,
			self.max_total_content_chars // len(results),
		)
		sources = []
		for result in results:
			item = result.item
			content = item.content or item.summary or ""
			evidence, truncated = _bounded_content(content, source_budget)
			sources.append(
				ContextEvidence(
					source_id=item.source_item_id,
					source_type=item.source,
					title=item.title,
					date=item.modified_at or item.file_created_at,
					evidence=evidence,
					trusted_source_reference=TrustedSourceReference(
						location=item.location,
						web_url=item.web_url,
						file_path=item.file_path,
						parent_location=item.parent_location,
						metadata=item.source_metadata,
					),
					truncated=truncated,
				)
			)
		return RagContext(query=query, sources=tuple(sources))


def _bounded_content(content: str, budget: int) -> tuple[str, bool]:
	content = content.strip()
	if len(content) <= budget:
		return content, False
	if budget <= len(_TRUNCATION_MARKER):
		return content[:budget], True
	return (
		content[: budget - len(_TRUNCATION_MARKER)].rstrip() + _TRUNCATION_MARKER,
		True,
	)
