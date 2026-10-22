import unittest

from sqlalchemy.orm import sessionmaker

from app.schemas import KnowledgeItemCreate
from app.ingestion.catalog import (
	create_knowledge_item,
	get_knowledge_item,
	list_knowledge_items,
)
from tests._postgres_test_db import create_postgres_test_engine


class KnowledgeItemServiceTests(unittest.TestCase):
	def setUp(self):
		self.engine, self.cleanup_database = create_postgres_test_engine()
		self.session_factory = sessionmaker(bind=self.engine)
		self.db = self.session_factory()

	def tearDown(self):
		self.db.close()
		self.cleanup_database()

	def test_create_persists_and_returns_knowledge_item(self):
		payload = KnowledgeItemCreate(
			source="local",
			source_item_id="item-1",
			title="Project notes",
			summary="Planning notes",
		)

		item = create_knowledge_item(self.db, payload)

		self.assertIsNotNone(item.id)
		self.assertEqual(item.source, "local")
		self.assertEqual(item.source_item_id, "item-1")
		self.assertEqual(item.title, "Project notes")
		self.assertIsNotNone(item.created_at)
		self.assertIsNotNone(self.db.get(type(item), item.id))

	def test_get_returns_none_for_missing_knowledge_item(self):
		self.assertIsNone(get_knowledge_item(self.db, 999))

	def test_list_uses_stable_order_and_pagination(self):
		for source_item_id in ("item-1", "item-2", "item-3"):
			create_knowledge_item(
				self.db,
				KnowledgeItemCreate(
					source="local", source_item_id=source_item_id
				),
			)

		items = list_knowledge_items(self.db, offset=1, limit=1)

		self.assertEqual(len(items), 1)
		self.assertEqual(items[0].source_item_id, "item-2")


if __name__ == "__main__":
	unittest.main()
