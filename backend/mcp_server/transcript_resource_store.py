import uuid

_chunk_cache: dict[str, str] = {}


def store_chunk(chunk_text: str) -> str:
    """Store a single transcript chunk in memory and return its resource ID."""
    chunk_id = str(uuid.uuid4())[:8]
    _chunk_cache[chunk_id] = chunk_text
    return chunk_id


def get_chunk(chunk_id: str) -> str | None:
    """Retrieve a cached transcript chunk by its resource ID."""
    return _chunk_cache.get(chunk_id)


def list_chunk_ids() -> list[str]:
    """List all currently cached transcript chunk resource IDs."""
    return list(_chunk_cache.keys())
