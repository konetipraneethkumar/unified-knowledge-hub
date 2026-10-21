"""Application orchestration for grounded answer generation."""
from dataclasses import dataclass
from datetime import datetime

from app.retrieval.context_builder import RagContext, TrustedSourceReference
from app.llm.providers import LLMProvider


@dataclass(frozen=True)
class AnswerSource:
	"""Trusted citation data retained outside generated answer text."""

	source_id: str
	source_type: str
	title: str | None
	date: datetime | None
	evidence: str
	trusted_source_reference: TrustedSourceReference


@dataclass(frozen=True)
class GroundedAnswer:
	answer: str
	sources: tuple[AnswerSource, ...]


def generate_grounded_answer(
	query: str,
	context: RagContext,
	provider: LLMProvider,
) -> GroundedAnswer:
	"""Call the provider with prompt-safe context and attach app-owned sources."""
	answer = provider.generate_answer(query, context.to_llm_context())
	return GroundedAnswer(
		answer=answer,
		sources=tuple(
			AnswerSource(
				source_id=source.source_id,
				source_type=source.source_type,
				title=source.title,
				date=source.date,
				evidence=source.evidence,
				trusted_source_reference=source.trusted_source_reference,
			)
			for source in context.sources
		),
	)
