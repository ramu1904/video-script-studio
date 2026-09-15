from unittest.mock import MagicMock, patch

from backend.mcp_server.search_functions import search_news, search_web


def test_search_news_parses_feed_entries():
    fake_entry = {
        "title": "Sample News Title",
        "link": "https://news.google.com/rss/articles/fake123",
        "published": "Mon, 14 Sep 2026 01:36:10 GMT",
        "source": {"title": "Sample Source"},
    }
    fake_feed = MagicMock()
    fake_feed.entries = [fake_entry]

    with patch("backend.mcp_server.search_functions.feedparser.parse", return_value=fake_feed):
        results = search_news("some topic", max_results=5)

    assert len(results) == 1
    assert results[0]["title"] == "Sample News Title"
    assert results[0]["source"] == "Sample Source"


def test_search_news_handles_spaces_in_query():
    fake_feed = MagicMock()
    fake_feed.entries = []

    with patch(
        "backend.mcp_server.search_functions.feedparser.parse", return_value=fake_feed
    ) as mock_parse:
        search_news("query with spaces", max_results=5)
        called_url = mock_parse.call_args[0][0]
        assert " " not in called_url


def test_search_news_dedupes_by_source():
    entries = [
        {
            "title": "First article",
            "link": "https://news.google.com/a1",
            "published": "Mon, 14 Sep 2026 01:00:00 GMT",
            "source": {"title": "Same Outlet"},
        },
        {
            "title": "Second article, same outlet",
            "link": "https://news.google.com/a2",
            "published": "Mon, 14 Sep 2026 02:00:00 GMT",
            "source": {"title": "Same Outlet"},
        },
        {
            "title": "Third article, different outlet",
            "link": "https://news.google.com/a3",
            "published": "Mon, 14 Sep 2026 03:00:00 GMT",
            "source": {"title": "Different Outlet"},
        },
    ]
    fake_feed = MagicMock()
    fake_feed.entries = entries

    with patch("backend.mcp_server.search_functions.feedparser.parse", return_value=fake_feed):
        results = search_news("some topic", max_results=8)

    assert len(results) == 2
    assert results[0]["source"] == "Same Outlet"
    assert results[1]["source"] == "Different Outlet"


def test_search_web_parses_ddgs_results():
    fake_result = {
        "title": "Sample Web Result",
        "href": "https://example.com/article",
        "body": "Sample snippet text",
    }
    mock_ddgs_instance = MagicMock()
    mock_ddgs_instance.__enter__.return_value.text.return_value = [fake_result]

    with patch("backend.mcp_server.search_functions.DDGS", return_value=mock_ddgs_instance):
        results = search_web("some query", max_results=5)

    assert len(results) == 1
    assert results[0]["title"] == "Sample Web Result"
    assert results[0]["url"] == "https://example.com/article"


def test_search_web_dedupes_by_domain():
    fake_results = [
        {"title": "First", "href": "https://example.com/article-1", "body": "..."},
        {
            "title": "Second, same domain",
            "href": "https://www.example.com/article-2",
            "body": "...",
        },
        {"title": "Third, different domain", "href": "https://other.com/article-3", "body": "..."},
    ]
    mock_ddgs_instance = MagicMock()
    mock_ddgs_instance.__enter__.return_value.text.return_value = fake_results

    with patch("backend.mcp_server.search_functions.DDGS", return_value=mock_ddgs_instance):
        results = search_web("some query", max_results=8)

    assert len(results) == 2
    assert results[0]["url"] == "https://example.com/article-1"
    assert results[1]["url"] == "https://other.com/article-3"
