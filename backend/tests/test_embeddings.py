import os
import unittest
from unittest.mock import patch

from app.core.config import Settings
from app.services.embeddings import EmbeddingService, MockEmbeddingService


class EmbeddingServiceTests(unittest.TestCase):
    def test_mock_returns_stable_vectors_with_configured_dimensions(self):
        service: EmbeddingService = MockEmbeddingService(dimensions=12)
        texts = ["first document", "second document"]

        first_result = service.embed(texts)
        second_result = service.embed(texts)

        self.assertEqual(first_result, second_result)
        self.assertEqual(len(first_result), len(texts))
        self.assertTrue(all(len(vector) == 12 for vector in first_result))
        self.assertNotEqual(first_result[0], first_result[1])

    def test_mock_rejects_non_positive_dimensions(self):
        with self.assertRaises(ValueError):
            MockEmbeddingService(dimensions=0)

    def test_embedding_settings_are_loaded_from_environment(self):
        environment = {
            "DATABASE_URL": "sqlite://",
            "EMBEDDING_PROVIDER": "custom-provider",
            "EMBEDDING_MODEL": "test-model",
            "EMBEDDING_API_KEY": "test-secret",
            "EMBEDDING_BASE_URL": "https://embeddings.example.test",
            "EMBEDDING_DIMENSIONS": "24",
        }
        with patch.dict(os.environ, environment, clear=True):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.EMBEDDING_PROVIDER, "custom-provider")
        self.assertEqual(settings.EMBEDDING_MODEL, "test-model")
        self.assertEqual(
            settings.EMBEDDING_API_KEY.get_secret_value(), "test-secret"
        )
        self.assertEqual(
            settings.EMBEDDING_BASE_URL,
            "https://embeddings.example.test",
        )
        self.assertEqual(settings.EMBEDDING_DIMENSIONS, 24)


if __name__ == "__main__":
    unittest.main()