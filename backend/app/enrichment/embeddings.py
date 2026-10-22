import hashlib
from collections.abc import Sequence
from math import isfinite, sqrt
from typing import Protocol

from app.core.config import settings


class EmbeddingService(Protocol):
	def embed(self, texts: Sequence[str]) -> list[list[float]]:
		"""Return one embedding vector for each input text."""
		...


class MockEmbeddingService:
	def __init__(self, dimensions: int = 8):
		if dimensions < 1:
			raise ValueError("dimensions must be a positive integer")
		self.dimensions = dimensions

	def embed(self, texts: Sequence[str]) -> list[list[float]]:
		vectors = []
		for text in texts:
			digest = hashlib.shake_256(text.encode("utf-8")).digest(
				self.dimensions * 4
			)
			vector = [
				int.from_bytes(digest[index : index + 4], "big")
				/ 0xFFFFFFFF
				* 2.0
				- 1.0
				for index in range(0, len(digest), 4)
			]
			vectors.append(vector)
		return vectors


def get_embedding_service() -> EmbeddingService:
	if settings.EMBEDDING_PROVIDER.lower() != "mock":
		raise RuntimeError(
			f"No embedding service is registered for provider "
			f"{settings.EMBEDDING_PROVIDER!r}"
		)
	return MockEmbeddingService(dimensions=settings.EMBEDDING_DIMENSIONS)


def validate_embedding(embedding: Sequence[float]) -> list[float]:
	vector = [float(value) for value in embedding]
	if not vector or not all(isfinite(value) for value in vector):
		raise ValueError("embedding must contain finite values")
	if not any(vector):
		raise ValueError("embedding must not be a zero vector")
	return vector


def mean_embedding(embeddings: list[list[float]]) -> list[float]:
	if not embeddings or any(
		len(embedding) != len(embeddings[0]) for embedding in embeddings
	):
		raise ValueError("embedding vectors must have matching dimensions")
	mean = [
		sum(embedding[index] for embedding in embeddings) / len(embeddings)
		for index in range(len(embeddings[0]))
	]
	norm = sqrt(sum(value * value for value in mean))
	if norm == 0:
		return embeddings[0]
	return [value / norm for value in mean]
