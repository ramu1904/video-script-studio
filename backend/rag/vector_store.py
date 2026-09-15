import os
import uuid

os.environ["ANONYMIZED_TELEMETRY"] = "False"

import chromadb

from backend.config import get_settings
from backend.rag.embedder import embed_texts

_client = None


def _get_client():
    """Lazily create a single persistent Chroma client, reused across calls.
    Telemetry is disabled via environment variable since it's set before
    chromadb is imported."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def create_transcript_collection(chunks: list[str]) -> str:
    """Embed and store a list of text chunks in a brand-new, uniquely-named
    Chroma collection. Returns the collection name for later querying."""
    client = _get_client()
    collection_name = f"transcript_{uuid.uuid4().hex[:8]}"
    collection = client.create_collection(name=collection_name)

    embeddings = embed_texts(chunks)
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    collection.add(ids=ids, embeddings=embeddings, documents=chunks)

    return collection_name


def query_transcript_collection(collection_name: str, query: str, top_k: int = 5) -> list[str]:
    """Find the top_k most relevant chunks in a given collection for a query."""
    client = _get_client()
    collection = client.get_collection(name=collection_name)

    query_embedding = embed_texts([query])[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    return results["documents"][0] if results["documents"] else []
