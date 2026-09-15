from mcp.server.fastmcp import FastMCP

from backend.mcp_server.article_functions import fetch_article
from backend.mcp_server.resource_store import get_article, list_article_ids, store_article
from backend.mcp_server.search_functions import search_news, search_web

mcp = FastMCP("video-script-studio-research")


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


if __name__ == "__main__":
    mcp.run()
