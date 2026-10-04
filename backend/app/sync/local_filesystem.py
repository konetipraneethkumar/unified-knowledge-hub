from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.connectors.local_filesystem import scan_directory, sha256_file
from app.enrichment.embeddings import EmbeddingService, get_embedding_service
from app.ingestion.indexing import store_embedding
from app.ingestion.normalization import normalize_file_metadata
from app.ingestion.pipeline import process_file_content
from app.ingestion.extraction import SUPPORTED_EXTENSIONS
from app.ingestion.privacy import filter_file_metadata
from app.models import KnowledgeItem, KnowledgeItemEmbedding


def index_local_directory(
	db: Session,
	directory: str | Path,
	embedding_service: EmbeddingService | None = None,
	chunk_size: int = 1200,
	chunk_overlap: int = 150,
	*,
	owner_id: int | None = None,
	connector_id: str | None = None,
	device_id: str | None = None,
) -> list[KnowledgeItem]:
	"""Synchronize discovered files into the knowledge-item index."""
	if chunk_size < 1 or not 0 <= chunk_overlap < chunk_size:
		raise ValueError("chunk_overlap must be nonnegative and smaller than chunk_size")
	embedding_service = embedding_service or get_embedding_service()
	root = Path(directory).resolve()
	indexed_items = []
	eligible_paths = set()
	scan_errors: list[OSError] = []
	records = scan_directory(directory, errors=scan_errors)
	if scan_errors:
		raise OSError(
			f"Could not completely scan local folder {root}: {scan_errors[0]}"
		) from scan_errors[0]

	for record in records:
		location = str(Path(record.path).resolve())
		if record.extension.lower() not in SUPPORTED_EXTENSIONS:
			continue
		metadata = filter_file_metadata(normalize_file_metadata(record, location))
		if metadata is None:
			continue
		eligible_paths.add(location)

		try:
			content_hash = sha256_file(location)
		except OSError as error:
			item = _get_local_item(db, location, connector_id)
			if item is None:
				item = KnowledgeItem(
					owner_id=owner_id,
					connector_id=connector_id,
					device_id=device_id,
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
		item = _get_local_item(db, location, connector_id)
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
			item.owner_id = owner_id
			item.connector_id = connector_id
			item.device_id = device_id
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
				owner_id=owner_id,
				connector_id=connector_id,
				device_id=device_id,
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
				if _get_local_item(db, location, connector_id) is None:
					raise
				continue

		try:
			processed = process_file_content(
				location,
				embedding_service,
				chunk_size=chunk_size,
				chunk_overlap=chunk_overlap,
			)
			if processed.embedding is not None:
				store_embedding(db, item.id, processed.embedding)
			item.content = processed.content
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

	statement = select(KnowledgeItem).where(KnowledgeItem.source == "local")
	if connector_id is not None:
		statement = statement.where(KnowledgeItem.connector_id == connector_id)
	elif owner_id is not None:
		statement = statement.where(
			KnowledgeItem.owner_id == owner_id,
			KnowledgeItem.connector_id.is_(None),
		)
	for item in db.scalars(statement).all():
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
	db: Session, location: str, connector_id: str | None
) -> KnowledgeItem | None:
	statement = select(KnowledgeItem).where(
		KnowledgeItem.source == "local",
		KnowledgeItem.source_item_id == location,
	)
	if connector_id is None:
		statement = statement.where(KnowledgeItem.connector_id.is_(None))
	else:
		statement = statement.where(KnowledgeItem.connector_id == connector_id)
	return db.scalar(statement)


def _set_processing_error(
	db: Session, item: KnowledgeItem, error: Exception
) -> None:
	item.processing_status = "failed"
	item.processing_error = f"{type(error).__name__}: {error}"[:2000]
	db.commit()


def _is_beneath(path: Path, root: Path) -> bool:
	try:
		path.resolve().relative_to(root)
		return True
	except ValueError:
		return False