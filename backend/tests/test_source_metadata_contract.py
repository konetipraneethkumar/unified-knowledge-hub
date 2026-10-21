import unittest
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import sessionmaker

from app.enrichment.embeddings import MockEmbeddingService
from app.ingestion.sources import SourceDocument, index_source_documents
from app.models import Connector, KnowledgeItem, User
from app.schemas import KnowledgeItemRead
from _postgres_test_db import create_postgres_test_engine


class SourceMetadataContractTests(unittest.TestCase):
	def setUp(self):
		self.engine, self.cleanup_database = create_postgres_test_engine()
		self.session_factory = sessionmaker(bind=self.engine)
		self.db = self.session_factory()

	def tearDown(self):
		self.db.close()
		self.cleanup_database()

	def test_connector_metadata_survives_ingestion_and_retrieval_serialization(self):
		user = User(email="source-metadata@example.test", password_hash=None)
		self.db.add(user)
		self.db.flush()
		connector = Connector(
			id=str(uuid4()),
			owner_id=user.id,
			device_id=None,
			connector_type="GMAIL",
			provider="google",
			name="Mail",
		)
		self.db.add(connector)
		self.db.commit()

		message_date = datetime(2026, 9, 18, 10, tzinfo=timezone.utc)
		document = SourceDocument(
			source_item_id="message-1",
			title="Mentor-Mentee Discussion",
			content="Mentor discussed academic progress.",
			source="gmail",
			item_type="email",
			modified_at=message_date,
			location="https://mail.google.com/mail/u/0/#all/thread-1",
			web_url="https://mail.google.com/mail/u/0/#all/thread-1",
			source_metadata={
				"sender": "mentor@cmr.edu.in",
				"subject": "Mentor-Mentee Discussion",
				"message_id": "message-1",
				"thread_id": "thread-1",
			},
		)

		result = index_source_documents(
			self.db,
			connector,
			[document],
			MockEmbeddingService(dimensions=16),
		)
		item = self.db.query(KnowledgeItem).one()
		response = KnowledgeItemRead.model_validate(item)

		self.assertEqual(result.processed, 1)
		self.assertEqual(response.source_type, "gmail")
		self.assertEqual(response.external_id, "message-1")
		self.assertEqual(response.title, "Mentor-Mentee Discussion")
		self.assertEqual(response.date, message_date)
		self.assertEqual(response.web_url, document.web_url)
		self.assertEqual(response.location, document.location)
		self.assertEqual(response.source_metadata, document.source_metadata)

		refreshed_document = replace(
			document,
			modified_at=datetime(2026, 9, 19, 10, tzinfo=timezone.utc),
			source_metadata={**document.source_metadata, "sender": "new-mentor@cmr.edu.in"},
		)
		refresh_result = index_source_documents(
			self.db,
			connector,
			[refreshed_document],
			MockEmbeddingService(dimensions=16),
		)
		self.db.refresh(item)
		refreshed_response = KnowledgeItemRead.model_validate(item)

		self.assertEqual(refresh_result.skipped, 1)
		self.assertEqual(
			refreshed_response.source_metadata["sender"], "new-mentor@cmr.edu.in"
		)
		self.assertEqual(refreshed_response.date, refreshed_document.modified_at)


if __name__ == "__main__":
	unittest.main()
