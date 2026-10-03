import hashlib
import tempfile
import unittest
from datetime import timezone
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import KnowledgeItem, KnowledgeItemEmbedding
from app.services.local_filesystem import index_local_directory


class LocalFilesystemIndexingTests(unittest.TestCase):
	def setUp(self):
		self.engine = create_engine(
			"sqlite://",
			connect_args={"check_same_thread": False},
			poolclass=StaticPool,
		)
		Base.metadata.create_all(self.engine)
		self.session_factory = sessionmaker(bind=self.engine)
		self.db = self.session_factory()

	def tearDown(self):
		self.db.close()
		Base.metadata.drop_all(self.engine)
		self.engine.dispose()

	def test_indexes_text_and_metadata_and_skips_unchanged_files(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			file_path = Path(temporary_directory) / "notes.txt"
			file_content = b"private file contents"
			file_path.write_bytes(file_content)
			file_stat = file_path.stat()

			first_index = index_local_directory(self.db, temporary_directory)
			second_index = index_local_directory(self.db, temporary_directory)

		self.assertEqual(len(first_index), 1)
		self.assertEqual(second_index, [])
		items = list(self.db.scalars(select(KnowledgeItem)).all())
		self.assertEqual(len(items), 1)
		item = items[0]
		canonical_path = str(file_path.resolve())
		self.assertEqual(item.source, "local")
		self.assertEqual(item.source_item_id, canonical_path)
		self.assertEqual(item.location, canonical_path)
		self.assertEqual(item.title, "notes.txt")
		self.assertEqual(item.item_type, "file")
		self.assertEqual(item.file_extension, ".txt")
		self.assertEqual(item.file_size_bytes, len(file_content))
		self.assertAlmostEqual(
			item.file_created_at.replace(tzinfo=timezone.utc).timestamp(),
			getattr(file_stat, "st_birthtime", file_stat.st_ctime),
			delta=0.00001,
		)
		self.assertAlmostEqual(
			item.modified_at.replace(tzinfo=timezone.utc).timestamp(),
			file_stat.st_mtime,
			delta=0.00001,
		)
		self.assertIsNone(item.summary)
		self.assertEqual(item.content_hash, hashlib.sha256(file_content).hexdigest())
		self.assertEqual(item.content, file_content.decode())
		self.assertEqual(item.processing_status, "processed")
		self.assertIsNone(item.processing_error)
		self.assertIsNotNone(
			self.db.get(KnowledgeItemEmbedding, item.id)
		)

	def test_hashes_identical_files_but_keeps_each_location(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			root = Path(temporary_directory)
			first_file = root / "first.txt"
			second_file = root / "nested" / "second.txt"
			different_file = root / "different.txt"
			second_file.parent.mkdir()
			first_file.write_bytes(b"same bytes")
			second_file.write_bytes(b"same bytes")
			different_file.write_bytes(b"different bytes")

			indexed_items = index_local_directory(self.db, root)
			repeated_index = index_local_directory(self.db, root)

		self.assertEqual(len(indexed_items), 3)
		self.assertEqual(repeated_index, [])
		items_by_name = {item.title: item for item in indexed_items}
		self.assertEqual(
			items_by_name["first.txt"].content_hash,
			items_by_name["second.txt"].content_hash,
		)
		self.assertNotEqual(
			items_by_name["first.txt"].content_hash,
			items_by_name["different.txt"].content_hash,
		)
		self.assertNotEqual(
			items_by_name["first.txt"].location,
			items_by_name["second.txt"].location,
		)
		self.assertEqual(
			len(list(self.db.scalars(select(KnowledgeItem)).all())), 3
		)

	def test_changed_file_updates_existing_knowledge_item_hash(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			file_path = Path(temporary_directory) / "changing.txt"
			file_path.write_bytes(b"first version")
			first_item = index_local_directory(self.db, temporary_directory)[0]
			first_hash = first_item.content_hash

			file_path.write_bytes(b"second version")
			updated_items = index_local_directory(self.db, temporary_directory)

		self.assertEqual(len(updated_items), 1)
		self.assertEqual(updated_items[0].id, first_item.id)
		self.assertNotEqual(updated_items[0].content_hash, first_hash)
		self.assertEqual(updated_items[0].content, "second version")
		self.assertEqual(updated_items[0].processing_status, "processed")
		self.assertEqual(
			len(list(self.db.scalars(select(KnowledgeItem)).all())), 1
		)

	def test_removes_deleted_and_unsupported_files_from_local_index(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			root = Path(temporary_directory)
			supported_file = root / "notes.txt"
			unsupported_file = root / "archive.exe"
			supported_file.write_text("indexed text", encoding="utf-8")
			unsupported_file.write_bytes(b"not indexed")
			indexed = index_local_directory(self.db, root)
			supported_file.unlink()
			index_local_directory(self.db, root)

		self.assertEqual(len(indexed), 1)
		self.assertEqual(list(self.db.scalars(select(KnowledgeItem)).all()), [])
		self.assertEqual(
			list(self.db.scalars(select(KnowledgeItemEmbedding)).all()), []
		)

	def test_redacts_credentials_before_content_is_stored(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			file_path = Path(temporary_directory) / "credentials.txt"
			file_path.write_text(
				"API_KEY=top-secret\nAuthorization: Bearer abc123",
				encoding="utf-8",
			)
			item = index_local_directory(self.db, temporary_directory)[0]

		self.assertNotIn("top-secret", item.content)
		self.assertNotIn("abc123", item.content)
		self.assertEqual(item.content.count("[REDACTED]"), 2)

	def test_failed_extraction_sets_error_and_retries_unchanged_file(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			file_path = Path(temporary_directory) / "retry.txt"
			file_path.write_text("retry content", encoding="utf-8")
			with patch(
				"app.services.local_filesystem.extract_document_text",
				side_effect=RuntimeError("temporary extractor failure"),
			):
				failed_item = index_local_directory(
					self.db, temporary_directory
				)[0]
			self.assertEqual(failed_item.processing_status, "failed")
			self.assertIn("temporary extractor failure", failed_item.processing_error)
			processed_item = index_local_directory(self.db, temporary_directory)[0]

		self.assertEqual(processed_item.processing_status, "processed")
		self.assertIsNone(processed_item.processing_error)

	def test_hash_failure_creates_failed_item_and_retries(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			file_path = Path(temporary_directory) / "hash-retry.txt"
			file_path.write_text("hash retry", encoding="utf-8")
			with patch(
				"app.services.local_filesystem.sha256_file",
				side_effect=OSError("temporary read failure"),
			):
				failed_item = index_local_directory(self.db, temporary_directory)[0]
			self.assertEqual(failed_item.processing_status, "failed")
			self.assertIn("temporary read failure", failed_item.processing_error)
			processed_item = index_local_directory(self.db, temporary_directory)[0]

		self.assertEqual(processed_item.processing_status, "processed")
		self.assertEqual(processed_item.content, "hash retry")

	def test_skips_file_with_credentials_in_its_path(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			file_path = Path(temporary_directory) / "notes_password=secret.txt"
			file_path.write_text("private", encoding="utf-8")

			with patch(
				"app.services.local_filesystem.sha256_file",
				side_effect=AssertionError("unsafe file contents were hashed"),
			):
				indexed_items = index_local_directory(
					self.db, temporary_directory
				)

		self.assertEqual(indexed_items, [])
		self.assertEqual(
			len(list(self.db.scalars(select(KnowledgeItem)).all())), 0
		)


if __name__ == "__main__":
	unittest.main()