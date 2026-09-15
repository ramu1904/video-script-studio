from mcp.server.fastmcp import FastMCP

from backend.mcp_server.article_functions import fetch_article
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
    and a representative image. Automatically decodes Google News redirect links."""
    return fetch_article(url)


if __name__ == "__main__":
    mcp.run()
