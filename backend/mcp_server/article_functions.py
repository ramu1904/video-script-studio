import re

import trafilatura
from googlenewsdecoder import gnewsdecoder

_MARKDOWN_IMAGE_PATTERN = re.compile(r"!\[.*?\]\(.*?\)")

_JUNK_LINE_PATTERNS = [
    re.compile(r"follow us on", re.IGNORECASE),
    re.compile(r"click here to", re.IGNORECASE),
    re.compile(r"subscribe to our", re.IGNORECASE),
    re.compile(r"download the .* app", re.IGNORECASE),
    re.compile(r"stay updated with the latest", re.IGNORECASE),
    re.compile(r"read more:", re.IGNORECASE),
    re.compile(r"also read:", re.IGNORECASE),
    re.compile(r"share this article", re.IGNORECASE),
]


def _resolve_google_news_url(url: str) -> str:
    """If this is a Google News redirect link, decode it to the real
    publisher URL. Otherwise, return the URL unchanged."""
    if "news.google.com" not in url:
        return url

    try:
        result = gnewsdecoder(url)
        if result.get("status") and result.get("decoded_url"):
            return result["decoded_url"]
    except Exception:
        pass

    return url


def _is_junk_line(line: str) -> bool:
    return any(pattern.search(line) for pattern in _JUNK_LINE_PATTERNS)


def _clean_text(text: str) -> str:
    """Remove embedded markdown image tags and common CTA/social-media
    boilerplate lines left over from extraction."""
    text = _MARKDOWN_IMAGE_PATTERN.sub("", text)

    lines = text.split("\n")
    cleaned_lines = [line for line in lines if line.strip() and not _is_junk_line(line)]

    return "\n".join(cleaned_lines).strip()


def fetch_article(url: str) -> dict:
    """Fetch a URL (including Google News redirect links) and extract
    clean article text, title, publish date, and a representative image.
    Returns a dict with any field set to None if it couldn't be found."""

    real_url = _resolve_google_news_url(url)

    downloaded = trafilatura.fetch_url(real_url)
    if downloaded is None:
        return {
            "resolved_url": real_url,
            "title": None,
            "text": None,
            "published_date": None,
            "image_url": None,
            "error": "Could not download the page (dead link, blocked, or timed out).",
        }

    result = trafilatura.bare_extraction(
        downloaded,
        with_metadata=True,
        include_images=True,
    )

    if result is None:
        return {
            "resolved_url": real_url,
            "title": None,
            "text": None,
            "published_date": None,
            "image_url": None,
            "error": "Page downloaded but no readable article content was found.",
        }

    raw_text = result.get("text")

    return {
        "resolved_url": result.get("url") or real_url,
        "title": result.get("title"),
        "text": _clean_text(raw_text) if raw_text else None,
        "published_date": result.get("date"),
        "image_url": result.get("image"),
        "error": None,
    }
