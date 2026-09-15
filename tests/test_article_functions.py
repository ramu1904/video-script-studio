from unittest.mock import patch

from backend.mcp_server.article_functions import fetch_article


def test_fetch_article_success():
    fake_extraction = {
        "url": "https://example.com/real-article",
        "title": "Sample Title",
        "text": "This is the clean article body.",
        "date": "2026-09-14",
        "image": "https://example.com/image.jpg",
    }

    with (
        patch(
            "backend.mcp_server.article_functions.trafilatura.fetch_url",
            return_value="<html>fake page</html>",
        ),
        patch(
            "backend.mcp_server.article_functions.trafilatura.bare_extraction",
            return_value=fake_extraction,
        ),
    ):
        result = fetch_article("https://example.com/real-article")

    assert result["error"] is None
    assert result["title"] == "Sample Title"
    assert result["text"] == "This is the clean article body."
    assert result["image_url"] == "https://example.com/image.jpg"


def test_fetch_article_download_fails():
    with patch("backend.mcp_server.article_functions.trafilatura.fetch_url", return_value=None):
        result = fetch_article("https://example.com/dead-link")

    assert result["error"] is not None
    assert result["title"] is None


def test_fetch_article_extraction_fails():
    with (
        patch(
            "backend.mcp_server.article_functions.trafilatura.fetch_url",
            return_value="<html>fake page</html>",
        ),
        patch(
            "backend.mcp_server.article_functions.trafilatura.bare_extraction",
            return_value=None,
        ),
    ):
        result = fetch_article("https://example.com/weird-page")

    assert result["error"] is not None
    assert result["text"] is None


def test_google_news_url_gets_decoded_before_fetching():
    fake_decode_result = {"status": True, "decoded_url": "https://realsite.com/article"}
    fake_extraction = {
        "url": "https://realsite.com/article",
        "title": "Decoded Article",
        "text": "Body text.",
        "date": None,
        "image": None,
    }

    with (
        patch("backend.mcp_server.article_functions.gnewsdecoder", return_value=fake_decode_result),
        patch(
            "backend.mcp_server.article_functions.trafilatura.fetch_url",
            return_value="<html>fake</html>",
        ) as mock_fetch,
        patch(
            "backend.mcp_server.article_functions.trafilatura.bare_extraction",
            return_value=fake_extraction,
        ),
    ):
        result = fetch_article("https://news.google.com/rss/articles/fake123")

        mock_fetch.assert_called_once_with("https://realsite.com/article")

    assert result["title"] == "Decoded Article"


def test_non_google_news_url_is_not_decoded():
    fake_extraction = {
        "url": "https://example.com/article",
        "title": "Direct Article",
        "text": "Body text.",
        "date": None,
        "image": None,
    }

    with (
        patch("backend.mcp_server.article_functions.gnewsdecoder") as mock_decoder,
        patch(
            "backend.mcp_server.article_functions.trafilatura.fetch_url",
            return_value="<html>fake</html>",
        ),
        patch(
            "backend.mcp_server.article_functions.trafilatura.bare_extraction",
            return_value=fake_extraction,
        ),
    ):
        fetch_article("https://example.com/article")

        mock_decoder.assert_not_called()


def test_markdown_image_tags_are_stripped_from_text():
    fake_extraction = {
        "url": "https://example.com/article",
        "title": "Article With Image",
        "text": "![some caption](https://example.com/pic.jpg)\nReal article content here.",
        "date": None,
        "image": "https://example.com/pic.jpg",
    }

    with (
        patch(
            "backend.mcp_server.article_functions.trafilatura.fetch_url",
            return_value="<html>fake</html>",
        ),
        patch(
            "backend.mcp_server.article_functions.trafilatura.bare_extraction",
            return_value=fake_extraction,
        ),
    ):
        result = fetch_article("https://example.com/article")

    assert "![" not in result["text"]
    assert "Real article content here." in result["text"]
