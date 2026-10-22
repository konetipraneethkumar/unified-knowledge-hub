from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.connectors.local_filesystem import scan_directory, sha256_file
from app.enrichment.embeddings import EmbeddingService, get_embedding_service
from app.ingestion.normalization import normalize_file_metadata
from app.ingestion.pipeline import process_file_content
from app.ingestion.extraction import SUPPORTED_EXTENSIONS
from app.ingestion.local_context import (
	LocalIndexContext,
	require_authorized_path,
	resolve_local_index_context,
)
from app.ingestion.privacy import filter_file_metadata
from app.models import KnowledgeItem, KnowledgeItemEmbedding


def index_local_directory(
	db: Session,
	directory: str | Path,
	*,
	owner_id: int,
	connector_id: str,
	device_id: str,
	embedding_service: EmbeddingService | None = None,
	chunk_size: int = 1200,
	chunk_overlap: int = 150,
) -> list[KnowledgeItem]:
	"""Index only files authorized for one owner, connector, and device."""
	if chunk_size < 1 or not 0 <= chunk_overlap < chunk_size:
		raise ValueError("chunk_overlap must be nonnegative and smaller than chunk_size")
	embedding_service = embedding_service or get_embedding_service()
	context = resolve_local_index_context(
		db, owner_id=owner_id, connector_id=connector_id, device_id=device_id
	)
	root = require_authorized_path(directory, context)
	indexed_items = []
	eligible_paths = set()

	for record in scan_directory(root):
		location = str(require_authorized_path(record.path, context))
		if record.extension.lower() not in SUPPORTED_EXTENSIONS:
			continue
		metadata = filter_file_metadata(normalize_file_metadata(record, location))
		if metadata is None:
			continue
		eligible_paths.add(location)

		try:
			content_hash = sha256_file(location)
		except OSError:
			item = _get_local_item(db, location, context)
			if item is None:
				item = KnowledgeItem(
					owner_id=context.owner_id,
					connector_id=context.connector_id,
					device_id=context.device_id,
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
			item.processing_error = "content_hash_failed"
			db.commit()
			db.refresh(item)
			indexed_items.append(item)
			continue

		metadata["content_hash"] = content_hash
		item = _get_local_item(db, location, context)
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
		try:
			processed = process_file_content(
				location,
				embedding_service,
				chunk_size=chunk_size,
				chunk_overlap=chunk_overlap,
			)
			if item is None:
				item = KnowledgeItem(
					owner_id=context.owner_id,
					connector_id=context.connector_id,
					device_id=context.device_id,
					source="local", source_item_id=metadata["path"], **item_metadata
				)
				db.add(item)
				db.flush()
			else:
				for field, value in item_metadata.items():
					setattr(item, field, value)
			item.indexed_at = datetime.now(timezone.utc)
			item.processing_status = "processed"
			item.processing_error = None
			if processed.embedding is not None:
				stored_embedding = db.get(KnowledgeItemEmbedding, item.id)
				if stored_embedding is None:
					db.add(
						KnowledgeItemEmbedding(
							item_id=item.id, embedding=processed.embedding
						)
					)
				else:
					stored_embedding.embedding = processed.embedding
			else:
				db.execute(
					delete(KnowledgeItemEmbedding).where(
						KnowledgeItemEmbedding.item_id == item.id
					)
				)
			db.commit()
		except IntegrityError:
			db.rollback()
			# A concurrent refresh won the race; leave its index untouched.
			continue
		except Exception:
			db.rollback()
			item = _get_local_item(db, location, context)
			if item is None:
				item = KnowledgeItem(
					owner_id=context.owner_id,
					connector_id=context.connector_id,
					device_id=context.device_id,
					source="local",
					source_item_id=metadata["path"],
					processing_status="failed",
					processing_error="processing_failed",
					**item_metadata,
				)
				db.add(item)
			else:
				_set_processing_error(db, item)
			db.commit()
		db.refresh(item)
		indexed_items.append(item)

	for item in db.scalars(
		select(KnowledgeItem).where(
			KnowledgeItem.source == "local",
			KnowledgeItem.owner_id == context.owner_id,
			KnowledgeItem.connector_id == context.connector_id,
			KnowledgeItem.device_id == context.device_id,
		)
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


def _get_local_item(
	db: Session, location: str, context: LocalIndexContext
) -> KnowledgeItem | None:
	return db.scalar(
		select(KnowledgeItem).where(
			KnowledgeItem.source == "local",
			KnowledgeItem.source_item_id == location,
			KnowledgeItem.owner_id == context.owner_id,
			KnowledgeItem.connector_id == context.connector_id,
			KnowledgeItem.device_id == context.device_id,
		)
	)


def _set_processing_error(db: Session, item: KnowledgeItem) -> None:
	item.processing_status = "failed"
	item.processing_error = "processing_failed"


def _is_beneath(path: Path, root: Path) -> bool:
	try:
		path.resolve().relative_to(root)
		return True
	except ValueError:
		return False
