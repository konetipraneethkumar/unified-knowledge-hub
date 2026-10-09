from datetime import datetime, timezone
import mimetypes
from math import sqrt
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.connectors.local_filesystem import scan_directory, sha256_file
from app.models import KnowledgeItem, KnowledgeItemEmbedding
from app.services.document_extraction import (
	SUPPORTED_EXTENSIONS,
	extract_document_text,
)
from app.services.embeddings import EmbeddingService, get_embedding_service
from app.services.vector_storage import store_embedding
from app.utils.privacy_filter import filter_file_content, filter_file_metadata


def index_local_directory(
	db: Session,
	directory: str | Path,
	embedding_service: EmbeddingService | None = None,
	chunk_size: int = 1200,
	chunk_overlap: int = 150,
) -> list[KnowledgeItem]:
	"""Index local-file metadata and embeddings without persisting extracted text."""
	if chunk_size < 1 or not 0 <= chunk_overlap < chunk_size:
		raise ValueError("chunk_overlap must be nonnegative and smaller than chunk_size")
	embedding_service = embedding_service or get_embedding_service()
	root = Path(directory).resolve()
	indexed_items = []
	eligible_paths = set()

	for record in scan_directory(directory):
		location = str(Path(record.path).resolve())
		if record.extension.lower() not in SUPPORTED_EXTENSIONS:
			continue
		metadata = filter_file_metadata(
			{
				"path": location,
				"filename": record.filename,
				"extension": record.extension,
				"size": record.size,
				"created_time": record.created_time,
				"modified_time": record.modified_time,
				"mime_type": mimetypes.guess_type(record.filename)[0],
			}
		)
		if metadata is None:
			continue
		eligible_paths.add(location)

		try:
			content_hash = sha256_file(location)
		except OSError as error:
			item = _get_local_item(db, location)
			if item is None:
				item = KnowledgeItem(
					source="local",
					source_item_id=location,
					title=metadata["filename"],
					item_type="file",
					mime_type=metadata["mime_type"],
					file_extension=metadata["extension"] or None,
					file_size_bytes=metadata["size"],
					file_created_at=metadata["created_time"],
					location=metadata["path"],
					modified_at=metadata["modified_time"],
					processing_status="failed",
				)
				db.add(item)
			item.processing_status = "failed"
			item.processing_error = f"{type(error).__name__}: {error}"[:2000]
			db.commit()
			db.refresh(item)
			indexed_items.append(item)
			continue

		metadata["content_hash"] = content_hash
		item = _get_local_item(db, location)
		if (
			item is not None
			and item.content_hash == content_hash
			and item.processing_status == "processed"
		):
			continue

		item_metadata = {
			"title": metadata["filename"],
			"item_type": "file",
			"mime_type": metadata["mime_type"],
			"file_extension": metadata["extension"] or None,
			"file_size_bytes": metadata["size"],
			"file_created_at": metadata["created_time"],
			"location": metadata["path"],
			"modified_at": metadata["modified_time"],
			"content_hash": metadata["content_hash"],
		}
		if item is not None:
			db.execute(
				delete(KnowledgeItemEmbedding).where(
					KnowledgeItemEmbedding.item_id == item.id
				)
			)
			for field, value in item_metadata.items():
				setattr(item, field, value)
			item.indexed_at = datetime.now(timezone.utc)
			item.content = None
			item.processing_status = "processing"
			item.processing_error = None
			db.commit()
		else:
			item = KnowledgeItem(
				source="local",
				source_item_id=metadata["path"],
				processing_status="processing",
				**item_metadata,
			)
			db.add(item)
			try:
				db.commit()
			except IntegrityError:
				db.rollback()
				if _get_local_item(db, location) is None:
					raise
				continue

		try:
			text = filter_file_content(extract_document_text(location))
			chunks = _chunk_text(text, chunk_size, chunk_overlap)
			if chunks:
				vectors = embedding_service.embed(chunks)
				if len(vectors) != len(chunks):
					raise ValueError(
						"embedding service returned an unexpected vector count"
					)
				embedding = _mean_vector(vectors)
				store_embedding(db, item.id, embedding)
			# Extracted text is transient: use it to build embeddings, then discard
			# it. The knowledge index stores metadata and vectors, not document text.
			item.content = None
			item.processing_status = "processed"
			item.processing_error = None
			db.commit()
		except Exception as error:
			db.rollback()
			item = db.get(KnowledgeItem, item.id)
			if item is None:
				continue
			_set_processing_error(db, item, error)
		db.refresh(item)
		indexed_items.append(item)

	for item in db.scalars(
		select(KnowledgeItem).where(KnowledgeItem.source == "local")
	).all():
		if (
			_is_beneath(Path(item.source_item_id), root)
			and item.source_item_id not in eligible_paths
		):
			db.execute(
				delete(KnowledgeItemEmbedding).where(
					KnowledgeItemEmbedding.item_id == item.id
				)
			)
			db.delete(item)
	db.commit()
	return indexed_items


def _get_local_item(db: Session, location: str) -> KnowledgeItem | None:
	return db.scalar(
		select(KnowledgeItem).where(
			KnowledgeItem.source == "local",
			KnowledgeItem.source_item_id == location,
		)
	)


def _set_processing_error(
	db: Session, item: KnowledgeItem, error: Exception
) -> None:
	item.processing_status = "failed"
	item.processing_error = f"{type(error).__name__}: {error}"[:2000]
	db.commit()


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
	text = text.strip()
	if not text:
		return []
	step = chunk_size - chunk_overlap
	return [
		text[start : start + chunk_size]
		for start in range(0, len(text), step)
	]


def _mean_vector(vectors: list[list[float]]) -> list[float]:
	if not vectors or any(len(vector) != len(vectors[0]) for vector in vectors):
		raise ValueError("embedding vectors must have matching dimensions")
	mean = [
		sum(vector[index] for vector in vectors) / len(vectors)
		for index in range(len(vectors[0]))
	]
	norm = sqrt(sum(value * value for value in mean))
	if norm == 0:
		return vectors[0]
	return [value / norm for value in mean]


def _is_beneath(path: Path, root: Path) -> bool:
	try:
		path.resolve().relative_to(root)
		return True
	except ValueError:
		return False
