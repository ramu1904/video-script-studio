from unittest.mock import patch

from backend.mcp_server.resource_store import get_article, list_article_ids, store_article
from backend.mcp_server.server import fetch_article_tool, read_cached_article


def test_store_and_retrieve_article():
    article_data = {
        "title": "Test Article",
        "text": "Some content",
        "resolved_url": "https://x.com",
    }
    article_id = store_article(article_data)

    retrieved = get_article(article_id)

    assert retrieved == article_data
    assert article_id in list_article_ids()


def test_get_article_returns_none_for_unknown_id():
    assert get_article("nonexistent-id-xyz") is None


def test_fetch_article_tool_caches_successful_fetch():
    fake_article = {
        "resolved_url": "https://example.com",
        "title": "Cached Title",
        "text": "Cached body",
        "published_date": None,
        "image_url": None,
        "error": None,
    }

    with patch("backend.mcp_server.server.fetch_article", return_value=fake_article):
        result = fetch_article_tool("https://example.com")

    assert "resource_id" in result
    assert get_article(result["resource_id"])["title"] == "Cached Title"


def test_fetch_article_tool_does_not_cache_on_error():
    fake_article = {
        "resolved_url": None,
        "title": None,
        "text": None,
        "published_date": None,
        "image_url": None,
        "error": "Could not download the page.",
    }

    with patch("backend.mcp_server.server.fetch_article", return_value=fake_article):
        result = fetch_article_tool("https://dead-link.com")

    assert "resource_id" not in result


def test_read_cached_article_returns_formatted_text():
    article_data = {
        "title": "Resource Test",
        "resolved_url": "https://x.com",
        "published_date": "2026-09-14",
        "text": "The actual article body.",
    }
    article_id = store_article(article_data)

    content = read_cached_article(article_id)

    assert "Resource Test" in content
    assert "The actual article body." in content


def test_read_cached_article_handles_missing_id():
    content = read_cached_article("does-not-exist")
    assert "No cached article found" in content
