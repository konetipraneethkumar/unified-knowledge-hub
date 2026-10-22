from dataclasses import dataclass
from pathlib import Path

from app.enrichment.embeddings import EmbeddingService, mean_embedding
from app.ingestion.chunking import chunk_text
from app.ingestion.extraction import extract_document_text
from app.ingestion.privacy import filter_file_content


@dataclass(frozen=True)
class ProcessedContent:
	embedding: list[float] | None


def process_file_content(
	path: str | Path,
	embedding_service: EmbeddingService,
	*,
	chunk_size: int = 1200,
	chunk_overlap: int = 150,
) -> ProcessedContent:
	content = filter_file_content(extract_document_text(path))
	chunks = chunk_text(content, chunk_size, chunk_overlap)
	if not chunks:
		return ProcessedContent(embedding=None)

	embeddings = embedding_service.embed(chunks)
	if len(embeddings) != len(chunks):
		raise ValueError("embedding service returned an unexpected vector count")
	return ProcessedContent(
		embedding=mean_embedding(embeddings),
	)
