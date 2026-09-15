from mcp.server.fastmcp import FastMCP

from backend.mcp_server.article_functions import fetch_article
from backend.mcp_server.prompt_loader import load_prompt_template
from backend.mcp_server.resource_store import get_article, list_article_ids, store_article
from backend.mcp_server.search_functions import search_news, search_web

mcp = FastMCP("video-script-studio-research")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def search_news_tool(query: str, max_results: int = 8) -> list[dict]:
    """Search Google News for recent and past articles on a topic.
    Returns up to max_results articles from different outlets, deduplicated by source."""
    return search_news(query, max_results=max_results)


@mcp.tool()
def search_web_tool(query: str, max_results: int = 8) -> list[dict]:
    """General web search for background/context info not limited to news.
    Returns up to max_results results from different domains, deduplicated."""
    return search_web(query, max_results=max_results)


@mcp.tool()
def fetch_article_tool(url: str) -> dict:
    """Fetch a specific article URL and extract clean text, title, publish date,
    and a representative image. Automatically decodes Google News redirect links.
    Also caches the result as an MCP Resource (article://<id>) for later re-reading
    without re-fetching."""
    article_data = fetch_article(url)
    if article_data.get("error") is None:
        resource_id = store_article(article_data)
        article_data["resource_id"] = resource_id
    return article_data


@mcp.tool()
def list_cached_articles_tool() -> list[str]:
    """List the resource IDs of all articles cached so far this session."""
    return list_article_ids()


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("article://{article_id}")
def read_cached_article(article_id: str) -> str:
    """Read a previously fetched article back out by its resource ID,
    without re-fetching it from the web."""
    article = get_article(article_id)
    if article is None:
        return f"No cached article found for id '{article_id}'."
    return (
        f"Title: {article.get('title')}\n"
        f"URL: {article.get('resolved_url')}\n"
        f"Published: {article.get('published_date')}\n\n"
        f"{article.get('text')}"
    )


# ---------------------------------------------------------------------------
# Prompts — the 9 narrative style templates
# ---------------------------------------------------------------------------


@mcp.prompt()
def style_news(topic: str, source_material: str, duration_seconds: int) -> str:
    """Straight, measured, factual news-anchor style."""
    return load_prompt_template("news", topic, source_material, duration_seconds)


@mcp.prompt()
def style_curiosity(topic: str, source_material: str, duration_seconds: int) -> str:
    """Curiosity-gap, hook-driven style ('Did you know...')."""
    return load_prompt_template("curiosity", topic, source_material, duration_seconds)


@mcp.prompt()
def style_documentary(topic: str, source_material: str, duration_seconds: int) -> str:
    """Calm, investigative documentary-narrator style."""
    return load_prompt_template("documentary", topic, source_material, duration_seconds)


@mcp.prompt()
def style_storytelling(topic: str, source_material: str, duration_seconds: int) -> str:
    """Narrative arc style with setup, complication, resolution."""
    return load_prompt_template("storytelling", topic, source_material, duration_seconds)


@mcp.prompt()
def style_dramatic(topic: str, source_material: str, duration_seconds: int) -> str:
    """Heightened stakes, tension-building dramatic style."""
    return load_prompt_template("dramatic", topic, source_material, duration_seconds)


@mcp.prompt()
def style_horror(topic: str, source_material: str, duration_seconds: int) -> str:
    """Ominous, dread-building horror-narrator style."""
    return load_prompt_template("horror", topic, source_material, duration_seconds)


@mcp.prompt()
def style_motivational(topic: str, source_material: str, duration_seconds: int) -> str:
    """Inspiring, energetic, call-to-action style."""
    return load_prompt_template("motivational", topic, source_material, duration_seconds)


@mcp.prompt()
def style_comedic(topic: str, source_material: str, duration_seconds: int) -> str:
    """Witty, satirical style (never mocking victims of real harm)."""
    return load_prompt_template("comedic", topic, source_material, duration_seconds)


@mcp.prompt()
def style_neutral(topic: str, source_material: str, duration_seconds: int) -> str:
    """Plain, clear explainer style with minimal embellishment."""
    return load_prompt_template("neutral", topic, source_material, duration_seconds)


if __name__ == "__main__":
    mcp.run()
