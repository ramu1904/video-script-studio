from unittest.mock import patch

from backend.graph.scriptwriter_node import (
    _clean_script_output,
    _split_into_sentences,
    _trim_to_word_target,
    write_script,
)


def test_clean_script_output_strips_markdown_bold():
    result = _clean_script_output("This is **bold** text.")
    assert "**" not in result
    assert "bold" in result


def test_clean_script_output_strips_title_line():
    result = _clean_script_output("Title: My Script\nActual content here.")
    assert "Title:" not in result
    assert "Actual content here." in result


def test_clean_script_output_strips_note_parenthetical():
    result = _clean_script_output("(Note: this follows the style guide)\nReal narration text.")
    assert "Note:" not in result
    assert "Real narration text." in result


def test_clean_script_output_strips_bracketed_stage_directions():
    result = _clean_script_output("Some text [pause] more text.")
    assert "[pause]" not in result


def test_clean_script_output_strips_dividers():
    result = _clean_script_output("First part.\n---\nSecond part.")
    assert "---" not in result


def test_split_into_sentences_splits_correctly():
    result = _split_into_sentences("First sentence. Second sentence! Third sentence?")
    assert result == ["First sentence.", "Second sentence!", "Third sentence?"]


def test_trim_to_word_target_keeps_text_under_target_unchanged():
    text = "One. Two. Three."
    result = _trim_to_word_target(text, word_target=50)
    assert result == text


def test_trim_to_word_target_stops_at_sentence_boundary_near_target():
    sentences = [f"This is sentence number {i}." for i in range(20)]
    text = " ".join(sentences)
    result = _trim_to_word_target(text, word_target=20)

    result_word_count = len(result.split())
    assert result_word_count <= 20 * 1.15
    assert result.rstrip().endswith(".")


def test_trim_to_word_target_always_includes_at_least_one_sentence():
    long_single_sentence = "This is one very long sentence with many many many words in it that exceeds the target by itself."
    result = _trim_to_word_target(long_single_sentence, word_target=5)
    assert len(result) > 0


def test_write_script_returns_expected_shape():
    with patch(
        "backend.graph.scriptwriter_node.call_llm",
        return_value="This is a clean generated script with several words in it for testing.",
    ):
        result = write_script(
            topic="Test Topic",
            source_material="Some facts.",
            style="news",
            duration_seconds=30,
        )

    assert "script" in result
    assert "word_count" in result
    assert "estimated_duration_seconds" in result
    assert result["word_count"] == len(result["script"].split())
