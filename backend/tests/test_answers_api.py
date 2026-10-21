from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import get_current_user
from app.llm.providers import (
	LLMConfigurationError,
	LLMProviderError,
	MockLLMProvider,
)
from app.main import app
from app.models import KnowledgeItem
from app.retrieval.hybrid import RankedKnowledgeItem


class RagAnswerApiTests(unittest.TestCase):
	def setUp(self):
		self.db = Mock()

		def override_get_db():
			yield self.db

		app.dependency_overrides[get_db] = override_get_db
		app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=7)
		self.client = TestClient(app)

	def tearDown(self):
		self.client.close()
		app.dependency_overrides.pop(get_db, None)
		app.dependency_overrides.pop(get_current_user, None)

	def _retrieval_result(self):
		item = KnowledgeItem(
			id=1,
			owner_id=7,
			source="google_drive",
			source_item_id="file-id",
			title="Academic report",
			content="The report describes semester performance.",
			file_path=r"C:\College\report.pdf",
			location=r"C:\College\report.pdf",
			source_metadata={
				"drive_file_id": "drive-id",
				"parent_ids": ["folder-id"],
				"access_token": "must-not-leak",
			},
		)
		return [RankedKnowledgeItem(item=item, relevance_score=1.0)]

	def test_answer_endpoint_returns_answer_and_app_owned_sources_separately(self):
		provider = MockLLMProvider(answer="The report describes performance.")
		with (
			patch(
				"app.api.search.hybrid_search",
				return_value=self._retrieval_result(),
			) as retrieval,
			patch("app.api.search.get_llm_provider", return_value=provider),
		):
			response = self.client.post(
				"/api/v1/search/ask",
				json={"query": "What does the report describe?"},
			)

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(
			payload["answer"], "The report describes performance."
		)
		self.assertEqual(payload["status"], "answered")
		self.assertEqual(payload["sources"][0]["source_id"], "file-id")
		self.assertEqual(payload["sources"][0]["title"], "Academic report")
		self.assertEqual(payload["sources"][0]["source_type"], "google_drive")
		self.assertEqual(
			payload["sources"][0]["evidence"],
			"The report describes semester performance.",
		)
		self.assertEqual(
			payload["sources"][0]["trusted_source_reference"]["file_path"],
			r"C:\College\report.pdf",
		)
		self.assertEqual(
			payload["sources"][0]["trusted_source_reference"]["metadata"],
			{"drive_file_id": "drive-id", "parent_ids": ["folder-id"]},
		)
		self.assertNotIn("must-not-leak", response.text)
		self.assertEqual(len(provider.calls), 1)
		self.assertEqual(
			provider.calls[0][0], "What does the report describe?"
		)
		self.assertNotIn("file-id", provider.calls[0][1])
		self.assertNotIn(r"C:\College\report.pdf", provider.calls[0][1])
		retrieval.assert_called_once()
		self.assertEqual(retrieval.call_args.kwargs["limit"], 5)
		self.assertEqual(retrieval.call_args.kwargs["owner_id"], 7)

	def test_empty_retrieval_returns_safe_response_without_calling_llm(self):
		with (
			patch(
				"app.api.search.hybrid_search",
				return_value=[],
			) as retrieval,
			patch("app.api.search.get_llm_provider") as get_provider,
		):
			response = self.client.post(
				"/api/v1/search/ask", json={"query": "What was discussed?"}
			)

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["status"], "no_results")
		self.assertEqual(payload["sources"], [])
		self.assertIn("couldn't find relevant information", payload["answer"])
		retrieval.assert_called_once()
		get_provider.assert_not_called()

	def test_answer_endpoint_reports_provider_timeout(self):
		with (
			patch(
				"app.api.search.hybrid_search",
				return_value=self._retrieval_result(),
			),
			patch(
				"app.api.search.get_llm_provider",
				side_effect=LLMProviderError(
					"Language model provider request timed out.",
					status_code=504,
				),
			),
		):
			response = self.client.post(
				"/api/v1/search/ask",
				json={"query": "What does the report describe?"},
			)

		self.assertEqual(response.status_code, 504)
		self.assertIn("timed out", response.json()["detail"])

	def test_answer_endpoint_reports_missing_provider_configuration(self):
		with (
			patch(
				"app.api.search.hybrid_search",
				return_value=self._retrieval_result(),
			),
			patch(
				"app.api.search.get_llm_provider",
				side_effect=LLMConfigurationError(
					"LLM_API_KEY is required."
				),
			),
		):
			response = self.client.post(
				"/api/v1/search/ask",
				json={"query": "What does the report describe?"},
			)

		self.assertEqual(response.status_code, 503)
		self.assertEqual(response.json()["detail"], "LLM_API_KEY is required.")

	def test_answer_endpoint_converts_unexpected_provider_failure(self):
		provider = Mock()
		provider.generate_answer.side_effect = RuntimeError("provider failure")
		with (
			patch(
				"app.api.search.hybrid_search",
				return_value=self._retrieval_result(),
			),
			patch("app.api.search.get_llm_provider", return_value=provider),
		):
			response = self.client.post(
				"/api/v1/search/ask",
				json={"query": "What does the report describe?"},
			)

		self.assertEqual(response.status_code, 502)
		self.assertEqual(
			response.json()["detail"],
			"The language model could not generate an answer.",
		)

	def test_answer_endpoint_rejects_blank_query(self):
		with patch("app.api.search.hybrid_search") as retrieval:
			response = self.client.post(
				"/api/v1/search/ask", json={"query": "   "}
			)

		self.assertEqual(response.status_code, 422)
		retrieval.assert_not_called()

	def test_answer_endpoint_requires_authentication(self):
		app.dependency_overrides.pop(get_current_user)
		try:
			response = self.client.post(
				"/api/v1/search/ask",
				json={"query": "What does the report describe?"},
			)
		finally:
			app.dependency_overrides[get_current_user] = (
				lambda: SimpleNamespace(id=7)
			)

		self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
	unittest.main()
