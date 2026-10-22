import unittest
from unittest.mock import patch

from app.ingestion.pipeline import process_file_content


class RecordingEmbeddingService:
	def __init__(self):
		self.texts = []

	def embed(self, texts):
		self.texts.extend(texts)
		return [[1.0, 0.0] for _ in texts]


class ProcessingPipelineTests(unittest.TestCase):
	def test_raw_text_is_redacted_for_embedding_and_not_returned(self):
		embeddings = RecordingEmbeddingService()
		with patch(
			"app.ingestion.pipeline.extract_document_text",
			return_value="API_KEY=top-secret\\nIndex this note",
		):
			processed = process_file_content("private.txt", embeddings)

		self.assertIsNotNone(processed.embedding)
		self.assertFalse(hasattr(processed, "content"))
		self.assertNotIn("top-secret", "\\n".join(embeddings.texts))


if __name__ == "__main__":
	unittest.main()
