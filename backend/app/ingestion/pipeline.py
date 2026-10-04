from dataclasses import dataclass
from pathlib import Path

from app.enrichment.embeddings import EmbeddingService, mean_embedding
from app.ingestion.chunking import chunk_text
from app.ingestion.extraction import extract_document_text
from app.ingestion.privacy import filter_file_content


@dataclass(frozen=True)
class ProcessedContent:
	content: str
	embedding: list[float] | None


def process_file_content(
	path: str | Path,
	embedding_service: EmbeddingService,
	*,
	chunk_size: int = 1200,
	chunk_overlap: int = 150,
) -> ProcessedContent:
	return process_text_content(
		extract_document_text(path),
		embedding_service,
		chunk_size=chunk_size,
		chunk_overlap=chunk_overlap,
	)


def process_text_content(
	content: str,
	embedding_service: EmbeddingService,
	*,
	chunk_size: int = 1200,
	chunk_overlap: int = 150,
) -> ProcessedContent:
	if chunk_size < 1 or not 0 <= chunk_overlap < chunk_size:
		raise ValueError("chunk_overlap must be nonnegative and smaller than chunk_size")
	content = filter_file_content(content)
	chunks = chunk_text(content, chunk_size, chunk_overlap)
	if not chunks:
		return ProcessedContent(content=content, embedding=None)

	embeddings = embedding_service.embed(chunks)
	if len(embeddings) != len(chunks):
		raise ValueError("embedding service returned an unexpected vector count")
	return ProcessedContent(
		content=content,
		embedding=mean_embedding(embeddings),
	)
