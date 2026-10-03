import hashlib
from typing import Protocol, Sequence

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