"""Normalize and persist documents returned by any connector."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.enrichment.embeddings import EmbeddingService, get_embedding_service
from app.ingestion.indexing import store_embedding
from app.ingestion.pipeline import process_text_content
from app.ingestion.privacy import filter_file_metadata
from app.models import Connector, KnowledgeItem, KnowledgeItemEmbedding


@dataclass(frozen=True)
class SourceDocument:
	source_item_id: str
	title: str
	content: str
	source: str
	item_type: str
	mime_type: str | None = None
	file_extension: str | None = None
	file_size_bytes: int | None = None
	file_created_at: datetime | None = None
	modified_at: datetime | None = None
	location: str | None = None
	processing_error: str | None = None


@dataclass(frozen=True)
class IngestionResult:
	processed: int
	skipped: int
	failed: int
	deleted: int
	errors: tuple[str, ...] = ()


def index_source_documents(
	db: Session,
	connector: Connector,
	documents: Iterable[SourceDocument],
	embedding_service: EmbeddingService | None = None,
) -> IngestionResult:
	"""Upsert a complete source snapshot, removing records no longer in that source."""
	service = embedding_service or get_embedding_service()
	seen_ids: set[str] = set()
	processed = skipped = failed = 0
	errors: list[str] = []

	for document in documents:
		safe_metadata = filter_file_metadata(
			{"filename": document.title, "path": document.location or ""}
		)
		if safe_metadata is None:
			continue
		seen_ids.add(document.source_item_id)
		content_hash = hashlib.sha256(document.content.encode("utf-8")).hexdigest()
		item = db.scalar(
			select(KnowledgeItem).where(
				KnowledgeItem.connector_id == connector.id,
				KnowledgeItem.source_item_id == document.source_item_id,
			)
		)
		if document.processing_error:
			if item is None:
				item = KnowledgeItem(
					owner_id=connector.owner_id,
					connector_id=connector.id,
					device_id=connector.device_id,
					source=document.source,
					source_item_id=document.source_item_id,
					title=safe_metadata["filename"],
					item_type=document.item_type,
					mime_type=document.mime_type,
					file_extension=document.file_extension,
					file_size_bytes=document.file_size_bytes,
					file_created_at=document.file_created_at,
					location=safe_metadata["path"] or None,
					modified_at=document.modified_at,
					processing_status="failed",
					processing_error=document.processing_error[:2000],
				)
				db.add(item)
			else:
				item.title = safe_metadata["filename"]
				item.location = safe_metadata["path"] or None
				item.modified_at = document.modified_at
				item.processing_status = "failed"
				item.processing_error = document.processing_error[:2000]
			db.commit()
			failed += 1
			errors.append(
				f"{document.title}: {document.processing_error}"[:500]
			)
			continue

		if item is None:
			item = KnowledgeItem(
				owner_id=connector.owner_id,
				connector_id=connector.id,
				device_id=connector.device_id,
				source=document.source,
				source_item_id=document.source_item_id,
				title=safe_metadata["filename"],
				item_type=document.item_type,
				mime_type=document.mime_type,
				file_extension=document.file_extension,
				file_size_bytes=document.file_size_bytes,
				file_created_at=document.file_created_at,
				location=safe_metadata["path"] or None,
				modified_at=document.modified_at,
				content_hash=content_hash,
				processing_status="processing",
			)
			db.add(item)
			db.flush()
		else:
			changed = item.content_hash != content_hash
			item.owner_id = connector.owner_id
			item.connector_id = connector.id
			item.device_id = connector.device_id
			item.source = document.source
			item.title = safe_metadata["filename"]
			item.item_type = document.item_type
			item.mime_type = document.mime_type
			item.file_extension = document.file_extension
			item.file_size_bytes = document.file_size_bytes
			item.file_created_at = document.file_created_at
			item.location = safe_metadata["path"] or None
			item.modified_at = document.modified_at
			if not changed and item.processing_status == "processed":
				skipped += 1
				continue

			db.execute(
				delete(KnowledgeItemEmbedding).where(
					KnowledgeItemEmbedding.item_id == item.id
				)
			)
			item.content_hash = content_hash
			item.content = None
			item.processing_status = "processing"
			item.processing_error = None

		item.indexed_at = datetime.now(timezone.utc)
		db.commit()
		item_id = item.id

		try:
			result = process_text_content(document.content, service)
			item = db.get(KnowledgeItem, item_id)
			if item is None:
				raise RuntimeError("Knowledge item disappeared during ingestion")
			if result.embedding is not None:
				store_embedding(db, item.id, result.embedding)
			item.content = result.content
			item.processing_status = "processed"
			item.processing_error = None
			db.commit()
			processed += 1
		except Exception as error:
			db.rollback()
			item = db.get(KnowledgeItem, item_id)
			if item is not None:
				item.processing_status = "failed"
				item.processing_error = f"{type(error).__name__}: {error}"[:2000]
				db.commit()
			failed += 1
			errors.append(f"{document.title}: {type(error).__name__}: {error}"[:500])

	existing_items = db.scalars(
		select(KnowledgeItem).where(KnowledgeItem.connector_id == connector.id)
	).all()
	deleted = 0
	for item in existing_items:
		if item.source_item_id not in seen_ids:
			db.delete(item)
			deleted += 1
	db.commit()
	return IngestionResult(processed, skipped, failed, deleted, tuple(errors))
