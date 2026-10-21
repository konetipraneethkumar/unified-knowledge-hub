import json
import unittest
from datetime import datetime, timezone

from app.models import KnowledgeItem
from app.retrieval.context_builder import RagContextBuilder
from app.retrieval.hybrid import RankedKnowledgeItem


def _ranked_item(**values) -> RankedKnowledgeItem:
	defaults = {
		"id": 1,
		"source": "local",
		"source_item_id": "file-1",
		"title": "Academic progress",
		"content": "Semester performance and progress.",
		"summary": None,
		"modified_at": None,
		"file_created_at": None,
		"location": None,
		"web_url": None,
		"file_path": None,
		"parent_location": None,
		"source_metadata": None,
	}
	defaults.update(values)
	return RankedKnowledgeItem(
		item=KnowledgeItem(**defaults),
		relevance_score=1.0,
	)


class RagContextBuilderTests(unittest.TestCase):
	def test_preserves_multiple_sources_and_separates_trusted_references(self):
		source_date = datetime(2026, 9, 18, 10, tzinfo=timezone.utc)
		results = [
			_ranked_item(
				source="gmail",
				source_item_id="message-1",
				title="Mentor discussion",
				content="Mentor discussed academic progress.",
				modified_at=source_date,
				location="https://mail.google.com/mail/u/0/#all/thread-1",
				web_url="https://mail.google.com/mail/u/0/#all/thread-1",
				source_metadata={"thread_id": "thread-1"},
			),
			_ranked_item(
				id=2,
				source="google_drive",
				source_item_id="drive-file-2",
				title="Semester report",
				content="Report evidence.",
				location="https://drive.google.com/file/d/drive-file-2",
				web_url="https://drive.google.com/file/d/drive-file-2",
			),
		]

		context = RagContextBuilder().build("What was discussed?", results)
		rendered = context.to_llm_context()
		prompt_data = json.loads(rendered)

		self.assertEqual([source.source_id for source in context.sources], [
			"message-1",
			"drive-file-2",
		])
		self.assertEqual(context.sources[0].date, source_date)
		self.assertEqual(
			context.sources[0].trusted_source_reference.metadata,
			{"thread_id": "thread-1"},
		)
		self.assertEqual(prompt_data["query"], "What was discussed?")
		self.assertEqual(len(prompt_data["evidence"]), 2)
		self.assertEqual(prompt_data["evidence"][0]["source_type"], "gmail")
		self.assertEqual(
			prompt_data["evidence"][0]["date"], source_date.isoformat()
		)
		for app_controlled_value in (
			"message-1",
			"drive-file-2",
			"mail.google.com",
			"drive.google.com",
			"thread-1",
		):
			self.assertNotIn(app_controlled_value, rendered)

	def test_empty_retrieval_has_no_evidence(self):
		context = RagContextBuilder().build("Any updates?", [])

		self.assertEqual(context.sources, ())
		self.assertEqual(json.loads(context.to_llm_context())["evidence"], [])

	def test_missing_optional_metadata_and_content_use_safe_defaults(self):
		context = RagContextBuilder().build(
			"Find progress", [_ranked_item(title=None, content=None)]
		)
		source = context.sources[0]
		payload = json.loads(context.to_llm_context())

		self.assertIsNone(source.title)
		self.assertIsNone(source.date)
		self.assertEqual(source.evidence, "")
		self.assertEqual(source.trusted_source_reference.location, None)
		self.assertIsNone(payload["evidence"][0]["date"])

	def test_long_content_is_truncated_with_per_source_and_total_limits(self):
		builder = RagContextBuilder(
			max_source_content_chars=80,
			max_total_content_chars=100,
		)
		context = builder.build(
			"Summarize",
			[
				_ranked_item(content="A" * 200),
				_ranked_item(
					id=2,
					source_item_id="file-2",
					content="B" * 200,
				),
			],
		)

		self.assertTrue(all(source.truncated for source in context.sources))
		self.assertTrue(
			all(len(source.evidence) <= 80 for source in context.sources)
		)
		self.assertLessEqual(
			sum(len(source.evidence) for source in context.sources), 100
		)
		self.assertTrue(all(
			source.evidence.endswith("[Evidence truncated]")
			for source in context.sources
		))

	def test_uses_summary_if_content_is_not_available(self):
		context = RagContextBuilder().build(
			"Summarize", [_ranked_item(content=None, summary="Indexed summary")]
		)

		self.assertEqual(context.sources[0].evidence, "Indexed summary")


if __name__ == "__main__":
	unittest.main()
