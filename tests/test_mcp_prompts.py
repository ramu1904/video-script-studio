from unittest.mock import patch

from backend.mcp_server.server import style_horror, style_news


def test_style_news_delegates_to_loader():
    with patch(
        "backend.mcp_server.server.load_prompt_template", return_value="fake prompt text"
    ) as mock_loader:
        result = style_news("Some Topic", "Some source material", 60)

        mock_loader.assert_called_once_with("news", "Some Topic", "Some source material", 60)

    assert result == "fake prompt text"


def test_style_horror_delegates_to_loader():
    with patch(
        "backend.mcp_server.server.load_prompt_template", return_value="fake horror prompt"
    ) as mock_loader:
        result = style_horror("Some Topic", "Some source material", 90)

        mock_loader.assert_called_once_with("horror", "Some Topic", "Some source material", 90)

    assert result == "fake horror prompt"
