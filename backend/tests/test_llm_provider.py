import json
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from app.core.config import Settings
from app.llm.providers import (
	GROUNDING_INSTRUCTIONS,
	LLMConfigurationError,
	LLMProviderError,
	MockLLMProvider,
	OpenAICompatibleProvider,
	get_llm_provider,
)
from app.llm.service import generate_grounded_answer
from app.models import KnowledgeItem
from app.retrieval.context_builder import RagContextBuilder
from app.retrieval.hybrid import RankedKnowledgeItem


class _Response:
	def __init__(self, payload: dict):
		self.payload = payload

	def __enter__(self):
		return self

	def __exit__(self, *_args):
		return False

	def read(self) -> bytes:
		return json.dumps(self.payload).encode("utf-8")


class LLMProviderTests(unittest.TestCase):
	def test_provider_sends_query_context_grounding_and_configuration(self):
		request_details = {}

		def fake_open(request, *, timeout):
			request_details["url"] = request.full_url
			request_details["authorization"] = request.get_header("Authorization")
			request_details["timeout"] = timeout
			request_details["payload"] = json.loads(request.data)
			return _Response(
				{"choices": [{"message": {"content": "Answer from evidence."}}]}
			)

		provider = OpenAICompatibleProvider(
			api_key="test-only-secret",
			model="chosen-model",
			base_url="https://llm.example.test/v1/",
			temperature=0.35,
			timeout_seconds=12,
			open_url=fake_open,
		)
		answer = provider.generate_answer(
			"What did the mentor say?",
			'{"evidence":[{"source_type":"gmail","content":"Discussed progress"}]}',
		)

		self.assertEqual(answer, "Answer from evidence.")
		self.assertEqual(
			request_details["url"],
			"https://llm.example.test/v1/chat/completions",
		)
		self.assertEqual(
			request_details["authorization"], "Bearer test-only-secret"
		)
		self.assertEqual(request_details["timeout"], 12)
		payload = request_details["payload"]
		self.assertEqual(payload["model"], "chosen-model")
		self.assertEqual(payload["temperature"], 0.35)
		self.assertEqual(payload["messages"][0]["role"], "system")
		for instruction in (
			"Answer only from the supplied context",
			"Do not invent facts",
			"document names",
			"locations",
			"URLs",
			"source IDs",
			"explicitly say",
		):
			self.assertIn(instruction, payload["messages"][0]["content"])
		user_message = payload["messages"][1]["content"]
		self.assertIn("What did the mentor say?", user_message)
		self.assertIn("Discussed progress", user_message)
		self.assertEqual(
			payload["messages"][0]["content"], GROUNDING_INSTRUCTIONS
		)

	def test_provider_timeout_is_reported_as_gateway_timeout(self):
		def timeout(*_args, **_kwargs):
			raise TimeoutError

		provider = OpenAICompatibleProvider(
			api_key="test-only-secret",
			model="chosen-model",
			base_url="https://llm.example.test/v1",
			temperature=0,
			timeout_seconds=1,
			open_url=timeout,
		)

		with self.assertRaises(LLMProviderError) as raised:
			provider.generate_answer("query", "{}")

		self.assertEqual(raised.exception.status_code, 504)
		self.assertIn("timed out", str(raised.exception))

	def test_mock_provider_can_be_injected_without_network_access(self):
		provider = MockLLMProvider(answer="Mocked grounded answer.")

		answer = provider.generate_answer("query", "context")

		self.assertEqual(answer, "Mocked grounded answer.")
		self.assertEqual(provider.calls, [("query", "context")])

	def test_trusted_references_are_attached_outside_provider_answer(self):
		timestamp = datetime(2026, 9, 18, tzinfo=timezone.utc)
		item = KnowledgeItem(
			id=1,
			source="gmail",
			source_item_id="message-id",
			title="Mentor discussion",
			content="Mentor discussed academic progress.",
			modified_at=timestamp,
			location="https://mail.google.com/mail/u/0/#all/thread-id",
			web_url="https://mail.google.com/mail/u/0/#all/thread-id",
			source_metadata={"thread_id": "thread-id"},
		)
		context = RagContextBuilder().build(
			"Summarize the discussion.",
			[RankedKnowledgeItem(item=item, relevance_score=1.0)],
		)
		provider = MockLLMProvider(answer="Mentor discussed progress.")

		result = generate_grounded_answer(
			"Summarize the discussion.", context, provider
		)

		self.assertEqual(result.answer, "Mentor discussed progress.")
		self.assertEqual(result.sources[0].source_id, "message-id")
		self.assertEqual(result.sources[0].date, timestamp)
		self.assertEqual(
			result.sources[0].evidence,
			"Mentor discussed academic progress.",
		)
		self.assertEqual(
			result.sources[0].trusted_source_reference.web_url,
			"https://mail.google.com/mail/u/0/#all/thread-id",
		)
		prompt_context = provider.calls[0][1]
		self.assertNotIn("message-id", prompt_context)
		self.assertNotIn("mail.google.com", prompt_context)
		self.assertNotIn("thread-id", prompt_context)

	def test_llm_settings_are_loaded_from_environment(self):
		with patch.dict(
			os.environ,
			{
				"DATABASE_URL": "postgresql://localhost/test",
				"LLM_PROVIDER": "openai_compatible",
				"LLM_MODEL": "test-model",
				"LLM_API_KEY": "test-secret",
				"LLM_BASE_URL": "https://llm.example.test/v1",
				"LLM_TEMPERATURE": "0.6",
				"LLM_TIMEOUT_SECONDS": "9",
			},
			clear=True,
		):
			settings = Settings(_env_file=None)

		self.assertEqual(settings.LLM_PROVIDER, "openai_compatible")
		self.assertEqual(settings.LLM_MODEL, "test-model")
		self.assertEqual(
			settings.LLM_API_KEY.get_secret_value(), "test-secret"
		)
		self.assertEqual(settings.LLM_BASE_URL, "https://llm.example.test/v1")
		self.assertEqual(settings.LLM_TEMPERATURE, 0.6)
		self.assertEqual(settings.LLM_TIMEOUT_SECONDS, 9)

	def test_external_provider_requires_a_nonempty_api_key(self):
		settings = type(
			"ProviderSettings",
			(),
			{
				"LLM_PROVIDER": "openai_compatible",
				"LLM_API_KEY": None,
			},
		)()
		with patch("app.llm.providers.settings", settings):
			with self.assertRaises(LLMConfigurationError):
				get_llm_provider()

		settings.LLM_API_KEY = type(
			"Secret", (), {"get_secret_value": lambda _self: " "}
		)()
		with patch("app.llm.providers.settings", settings):
			with self.assertRaises(LLMConfigurationError):
				get_llm_provider()


if __name__ == "__main__":
	unittest.main()
