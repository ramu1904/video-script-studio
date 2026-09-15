import pytest

from backend.mcp_server.prompt_loader import calculate_word_target, load_prompt_template


def test_word_target_matches_expected_values():
    assert calculate_word_target(30) == 75
    assert calculate_word_target(60) == 150
    assert calculate_word_target(90) == 225
    assert calculate_word_target(180) == 450
    assert calculate_word_target(480) == 1200


def test_load_prompt_template_fills_placeholders():
    result = load_prompt_template(
        style="neutral",
        topic="Test Topic",
        source_material="Some facts here.",
        duration_seconds=60,
    )
    assert "Test Topic" in result
    assert "Some facts here." in result
    assert "150 words" in result
    assert "{topic}" not in result
    assert "{source_material}" not in result


def test_load_prompt_template_raises_for_unknown_style():
    with pytest.raises(ValueError):
        load_prompt_template(
            style="nonexistent_style",
            topic="Test",
            source_material="Test",
            duration_seconds=60,
        )
