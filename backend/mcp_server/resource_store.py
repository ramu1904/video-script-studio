import uuid

_article_cache: dict[str, dict] = {}


def store_article(article_data: dict) -> str:
    """Store a fetched article in memory and return its resource ID."""
    article_id = str(uuid.uuid4())[:8]
    _article_cache[article_id] = article_data
    return article_id


def get_article(article_id: str) -> dict | None:
    """Retrieve a cached article by its resource ID."""
    return _article_cache.get(article_id)


def list_article_ids() -> list[str]:
    """List all currently cached article resource IDs."""
    return list(_article_cache.keys())
