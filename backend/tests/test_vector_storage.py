import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import KnowledgeItem, KnowledgeItemEmbedding
from app.schemas import KnowledgeItemCreate
from app.services.embeddings import MockEmbeddingService
from app.services.knowledge_items import create_knowledge_item
from app.services.vector_storage import (
	search_similar_knowledge_items,
	store_embedding,
)


class VectorStorageTests(unittest.TestCase):
	def setUp(self):
		self.engine = create_engine(
			"sqlite://",
			connect_args={"check_same_thread": False},
			poolclass=StaticPool,
		)
		Base.metadata.create_all(self.engine)
		self.session_factory = sessionmaker(bind=self.engine)
		self.db = self.session_factory()
		self.embedding_service = MockEmbeddingService(dimensions=16)

	def tearDown(self):
		self.db.close()
		Base.metadata.drop_all(self.engine)
		self.engine.dispose()

	def create_item(self, source_item_id: str) -> KnowledgeItem:
		return create_knowledge_item(
			self.db,
			KnowledgeItemCreate(
				source="local", source_item_id=source_item_id
			),
		)

	def test_stores_vectors_separately_and_searches_by_similarity(self):
		matching_item = self.create_item("matching")
		other_item = self.create_item("other")
		matching_vector, other_vector = self.embedding_service.embed(
			["matching text", "different text"]
		)

		stored = store_embedding(
			self.db, matching_item.id, matching_vector
		)
		store_embedding(self.db, other_item.id, other_vector)
		results = search_similar_knowledge_items(
			self.db, matching_vector, limit=2
		)

		self.assertEqual(stored.item_id, matching_item.id)
		self.assertIsInstance(
			self.db.get(KnowledgeItemEmbedding, matching_item.id),
			KnowledgeItemEmbedding,
		)
		self.assertFalse(hasattr(matching_item, "embedding"))
		self.assertEqual(results[0][0].id, matching_item.id)
		self.assertAlmostEqual(results[0][1], 1.0)
		self.assertEqual(len(results), 2)

	def test_storing_again_replaces_the_existing_vector(self):
		item = self.create_item("replace")
		first_vector, second_vector = self.embedding_service.embed(
			["first version", "second version"]
		)

		store_embedding(self.db, item.id, first_vector)
		stored = store_embedding(self.db, item.id, second_vector)

		self.assertEqual(stored.item_id, item.id)
		results = search_similar_knowledge_items(
			self.db, second_vector, limit=1
		)
		self.assertEqual(results[0][0].id, item.id)
		self.assertAlmostEqual(results[0][1], 1.0)


if __name__ == "__main__":
	unittest.main()