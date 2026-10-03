import unittest

from sqlalchemy.orm import sessionmaker

from app.enrichment.embeddings import MockEmbeddingService
from app.models import KnowledgeItem
from app.schemas import KnowledgeItemCreate
from app.ingestion.catalog import create_knowledge_item
from app.retrieval.hybrid import hybrid_search
from app.ingestion.indexing import store_embedding

from _postgres_test_db import create_postgres_test_engine


class HybridRetrievalTests(unittest.TestCase):
	def setUp(self):
		self.engine, self.cleanup_database = create_postgres_test_engine()
		self.session_factory = sessionmaker(bind=self.engine)
		self.db = self.session_factory()
		self.embedding_service = MockEmbeddingService(dimensions=16)

	def tearDown(self):
		self.db.close()
		self.cleanup_database()

	def create_item(self, source_item_id: str, title: str) -> KnowledgeItem:
		return create_knowledge_item(
			self.db,
			KnowledgeItemCreate(
				source="local",
				source_item_id=source_item_id,
				title=title,
			),
		)

	def test_hybrid_search_unions_sources_deduplicates_and_scores(self):
		query = "needle"
		overlap_item = self.create_item("overlap", "needle")
		keyword_only_item = self.create_item("keyword-only", "needle nearby")
		vector_only_item = self.create_item("vector-only", "unrelated title")
		query_vector = self.embedding_service.embed([query])[0]
		store_embedding(self.db, overlap_item.id, query_vector)
		store_embedding(self.db, vector_only_item.id, query_vector)

		results = hybrid_search(
			self.db,
			query,
			self.embedding_service,
			limit=10,
			rank_constant=0,
		)

		result_ids = [result.item.id for result in results]
		self.assertCountEqual(
			result_ids,
			[overlap_item.id, keyword_only_item.id, vector_only_item.id],
		)
		self.assertEqual(len(result_ids), len(set(result_ids)))
		self.assertEqual(result_ids[0], overlap_item.id)
		self.assertEqual(results[0].relevance_score, 2.0)
		self.assertTrue(
			all(result.relevance_score > 0 for result in results)
		)

	def test_hybrid_search_can_return_keyword_results_without_vectors(self):
		item = self.create_item("keyword-only", "needle in title")

		results = hybrid_search(self.db, "needle", self.embedding_service)

		self.assertEqual(len(results), 1)
		self.assertEqual(results[0].item.id, item.id)
		self.assertGreater(results[0].relevance_score, 0)


if __name__ == "__main__":
	unittest.main()
