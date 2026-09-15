from functools import lru_cache

from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it (loading is slow, ~1-2s)."""
    return SentenceTransformer(_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Convert a list of text strings into a list of embedding vectors."""
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()
