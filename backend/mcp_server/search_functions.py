from urllib.parse import quote, urlparse

import feedparser
from ddgs import DDGS


def search_news(query: str, max_results: int = 8) -> list[dict]:
    """Search Google News RSS for a query. Free, no API key needed.
    Returns up to max_results articles, deduplicated by source outlet."""
    encoded_query = quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)

    results = []
    seen_sources = set()

    for entry in feed.entries:
        source_name = entry.get("source", {}).get("title") if entry.get("source") else None
        dedup_key = source_name or entry.get("link")

        if dedup_key in seen_sources:
            continue
        seen_sources.add(dedup_key)

        results.append(
            {
                "title": entry.get("title"),
                "url": entry.get("link"),
                "published_date": entry.get("published"),
                "source": source_name,
            }
        )
        if len(results) >= max_results:
            break

    return results


def search_web(query: str, max_results: int = 8) -> list[dict]:
    """General web search via DuckDuckGo. Free, no API key needed.
    Returns up to max_results results, deduplicated by domain.
    Fetches a larger raw batch internally since some domains repeat."""
    raw_fetch_count = max_results * 4

    results = []
    seen_domains = set()

    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=raw_fetch_count):
            href = r.get("href", "")
            domain = urlparse(href).netloc.replace("www.", "")

            if domain in seen_domains:
                continue
            seen_domains.add(domain)

            results.append(
                {
                    "title": r.get("title"),
                    "url": href,
                    "snippet": r.get("body"),
                }
            )
            if len(results) >= max_results:
                break

    return results
