from datetime import datetime, timezone
import unittest

from pydantic import ValidationError

from app.models import KnowledgeItem
from app.schemas import KnowledgeItemCreate, KnowledgeItemRead


class KnowledgeItemSchemaTests(unittest.TestCase):
    def test_create_requires_non_empty_source_identifiers(self):
        invalid_payloads = [
            {"source_item_id": "item-1"},
            {"source": "local"},
            {"source": "", "source_item_id": "item-1"},
            {"source": "local", "source_item_id": ""},
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(ValidationError):
                    KnowledgeItemCreate(**payload)

    def test_create_excludes_internal_fields(self):
        with self.assertRaises(ValidationError):
            KnowledgeItemCreate(
                source="local",
                source_item_id="item-1",
                content_hash="internal-hash",
            )

    def test_read_serializes_orm_object_without_content_hash(self):
        timestamp = datetime.now(timezone.utc)
        item = KnowledgeItem(
            id=1,
            source="local",
            source_item_id="item-1",
            title="Notes",
            item_type="file",
            mime_type="text/plain",
            location="/notes.txt",
            summary="A short summary",
            created_at=timestamp,
            modified_at=None,
            indexed_at=timestamp,
            content_hash="internal-hash",
        )

        result = KnowledgeItemRead.model_validate(item)

        self.assertEqual(result.id, 1)
        self.assertEqual(result.source_item_id, "item-1")
        self.assertEqual(result.created_at, timestamp)
        self.assertNotIn("content_hash", result.model_dump())


if __name__ == "__main__":
    unittest.main()