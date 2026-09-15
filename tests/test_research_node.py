from unittest.mock import patch

from backend.graph.research_node import research_agent


def _fake_news_item(title, url, published_date="Mon, 14 Sep 2026", source="Outlet A"):
    return {"title": title, "url": url, "published_date": published_date, "source": source}


def _fake_web_item(title, url, snippet="A snippet."):
    return {"title": title, "url": url, "snippet": snippet}


def _fake_fetch_article_side_effect(url):
    """Returns a fetch_article-shaped result that reflects the URL it was
    actually called with, so tests can verify per-source correctness."""
    return {
        "resolved_url": url,
        "title": f"Fetched: {url}",
        "text": f"Full article body for {url}.",
        "published_date": "2026-09-14",
        "image_url": None,
        "error": None,
    }


def test_research_agent_combines_and_dedupes_by_domain():
    news_results = [
        _fake_news_item("News Article 1", "https://outleta.com/a1"),
        _fake_news_item("News Article 2", "https://outletb.com/a2"),
    ]
    web_results = [
        _fake_web_item("Web Article 1", "https://outleta.com/w1"),  # same domain as news 1
        _fake_web_item("Web Article 2", "https://outletc.com/w2"),
    ]

    with (
        patch("backend.graph.research_node.search_news", return_value=news_results),
        patch("backend.graph.research_node.search_web", return_value=web_results),
        patch(
            "backend.graph.research_node.fetch_article", side_effect=_fake_fetch_article_side_effect
        ),
    ):
        result = research_agent("some topic", max_sources=8, full_text_count=3)

    assert len(result["sources"]) == 3  # outleta, outletb, outletc — deduped
    urls = [s["url"] for s in result["sources"]]
    assert "https://outleta.com/a1" in urls
    assert "https://outletb.com/a2" in urls
    assert "https://outletc.com/w2" in urls


def test_research_agent_only_fetches_full_text_for_top_n():
    news_results = [
        _fake_news_item(f"Article {i}", f"https://outlet{i}.com/a{i}") for i in range(5)
    ]

    with (
        patch("backend.graph.research_node.search_news", return_value=news_results),
        patch("backend.graph.research_node.search_web", return_value=[]),
        patch(
            "backend.graph.research_node.fetch_article", side_effect=_fake_fetch_article_side_effect
        ) as mock_fetch,
    ):
        research_agent("some topic", max_sources=5, full_text_count=2)

    assert mock_fetch.call_count == 2


def test_research_agent_falls_back_to_snippet_when_fetch_fails():
    news_results = [_fake_news_item("Article 1", "https://outlet.com/a1")]

    failed_fetch = {
        "resolved_url": None,
        "title": None,
        "text": None,
        "published_date": None,
        "image_url": None,
        "error": "Could not download the page.",
    }

    with (
        patch("backend.graph.research_node.search_news", return_value=news_results),
        patch("backend.graph.research_node.search_web", return_value=[]),
        patch("backend.graph.research_node.fetch_article", return_value=failed_fetch),
    ):
        result = research_agent("some topic", max_sources=5, full_text_count=1)

    assert result["sources"][0]["url"] == "https://outlet.com/a1"
    assert "Article 1" in result["source_material"]


def test_research_agent_builds_labeled_source_material():
    news_results = [_fake_news_item("First Article", "https://outlet.com/a1")]

    with (
        patch("backend.graph.research_node.search_news", return_value=news_results),
        patch("backend.graph.research_node.search_web", return_value=[]),
        patch(
            "backend.graph.research_node.fetch_article", side_effect=_fake_fetch_article_side_effect
        ),
    ):
        result = research_agent("some topic", max_sources=5, full_text_count=1)

    assert "[Source 1: First Article]" in result["source_material"]
    assert "Full article body for https://outlet.com/a1." in result["source_material"]


def test_research_agent_respects_max_sources_cap():
    news_results = [
        _fake_news_item(f"Article {i}", f"https://outlet{i}.com/a{i}") for i in range(10)
    ]

    with (
        patch("backend.graph.research_node.search_news", return_value=news_results),
        patch("backend.graph.research_node.search_web", return_value=[]),
        patch(
            "backend.graph.research_node.fetch_article", side_effect=_fake_fetch_article_side_effect
        ),
    ):
        result = research_agent("some topic", max_sources=4, full_text_count=2)

    assert len(result["sources"]) == 4
