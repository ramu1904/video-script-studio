from unittest.mock import patch

from backend.mcp_server.server import fetch_article_tool, search_news_tool, search_web_tool


def test_search_news_tool_delegates_correctly():
    fake_results = [
        {"title": "Fake", "url": "https://example.com", "published_date": None, "source": "X"}
    ]

    with patch("backend.mcp_server.server.search_news", return_value=fake_results) as mock_search:
        result = search_news_tool("some query", max_results=3)

        mock_search.assert_called_once_with("some query", max_results=3)

    assert result == fake_results


def test_search_web_tool_delegates_correctly():
    fake_results = [{"title": "Fake", "url": "https://example.com", "snippet": "..."}]

    with patch("backend.mcp_server.server.search_web", return_value=fake_results) as mock_search:
        result = search_web_tool("some query", max_results=5)

        mock_search.assert_called_once_with("some query", max_results=5)

    assert result == fake_results


def test_fetch_article_tool_delegates_correctly():
    fake_article = {
        "resolved_url": "https://example.com",
        "title": "Fake Title",
        "text": "Fake body",
        "published_date": None,
        "image_url": None,
        "error": None,
    }

    with patch("backend.mcp_server.server.fetch_article", return_value=fake_article) as mock_fetch:
        result = fetch_article_tool("https://example.com")

        mock_fetch.assert_called_once_with("https://example.com")

    assert result == fake_article
