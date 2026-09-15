from urllib.parse import urlparse

from backend.mcp_server.article_functions import fetch_article
from backend.mcp_server.search_functions import search_news, search_web


_MAX_FULL_TEXT_CHARS = 1200  # roughly 200 words per full-text article, keeps token budget safe


def _domain_of(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "")


def _combine_and_dedupe(
    news_results: list[dict], web_results: list[dict], max_sources: int
) -> list[dict]:
    """Merge news + web results into one list, deduped by domain, capped at max_sources."""
    combined = []
    seen_domains = set()

    for item in news_results + web_results:
        url = item.get("url", "")
        domain = _domain_of(url)
        if domain in seen_domains:
            continue
        seen_domains.add(domain)
        combined.append(item)
        if len(combined) >= max_sources:
            break

    return combined


def research_agent(topic: str, max_sources: int = 8, full_text_count: int = 3) -> dict:
    """Research a topic: search news + web, fetch full text for the top few
    sources, and assemble both a structured source list (for the API response)
    and a plain-text source_material string (for the Script Writer prompt)."""

    news_results = search_news(topic, max_results=6)
    web_results = search_web(topic, max_results=4)
    combined = _combine_and_dedupe(news_results, web_results, max_sources)

    sources = []
    source_material_parts = []

    for i, item in enumerate(combined):
        is_full_text = i < full_text_count
        title = item.get("title")
        url = item.get("url")
        published_date = item.get("published_date")
        snippet = item.get("snippet")
        image_url = None
        body_text = snippet

        if is_full_text:
            article = fetch_article(url)
            if article.get("error") is None:
                url = article.get("resolved_url") or url
                image_url = article.get("image_url")
                published_date = article.get("published_date") or published_date
                full_text = article.get("text") or ""
                body_text = full_text[:_MAX_FULL_TEXT_CHARS]
            # if fetch_article failed, we silently fall back to the snippet
            # already set above, since not every source will be scrapable.

        sources.append(
            {
                "title": title,
                "url": url,
                "published_date": published_date,
                "snippet": snippet,
                "image_url": image_url,
            }
        )

        label = f"[Source {i + 1}: {title}]"
        source_material_parts.append(f"{label}\n{body_text or 'No content available.'}")

    source_material = "\n\n".join(source_material_parts)

    return {
        "sources": sources,
        "source_material": source_material,
    }
