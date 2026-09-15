from unittest.mock import patch

from backend.graph.editor_helper_node import (
    _default_editing_guidance,
    _parse_json_array,
    _split_into_sentences,
    generate_timeline,
)


def test_split_into_sentences_splits_correctly():
    result = _split_into_sentences("First sentence. Second sentence! Third one?")
    assert result == ["First sentence.", "Second sentence!", "Third one?"]


def test_parse_json_array_handles_clean_json():
    result = _parse_json_array('[{"shot_type": "b_roll"}]')
    assert result == [{"shot_type": "b_roll"}]


def test_parse_json_array_returns_empty_list_on_malformed_input():
    assert _parse_json_array("not json") == []


def test_generate_timeline_empty_script_returns_empty_list():
    assert generate_timeline("") == []


def test_generate_timeline_computes_correct_cumulative_timing():
    fake_guidance = [
        {
            "shot_type": "talking_head",
            "camera_angle": "x",
            "onscreen_text": "",
            "resource_suggestion": "",
        },
        {
            "shot_type": "b_roll",
            "camera_angle": "y",
            "onscreen_text": "",
            "resource_suggestion": "",
        },
    ]

    with patch(
        "backend.graph.editor_helper_node.call_llm",
        return_value=str(fake_guidance).replace("'", '"'),
    ):
        timeline = generate_timeline("First sentence here. Second sentence here.")

    assert len(timeline) == 2
    assert timeline[0]["start_seconds"] == 0.0
    assert timeline[1]["start_seconds"] == timeline[0]["end_seconds"]


def test_generate_timeline_falls_back_to_default_guidance_when_unparseable():
    with patch("backend.graph.editor_helper_node.call_llm", return_value="not valid json"):
        timeline = generate_timeline("One sentence here.")

    assert len(timeline) == 1
    assert timeline[0]["shot_type"] == "talking_head"


def test_generate_timeline_falls_back_when_guidance_list_shorter_than_sentences():
    fake_guidance = [
        {"shot_type": "b_roll", "camera_angle": "x", "onscreen_text": "", "resource_suggestion": ""}
    ]

    with patch(
        "backend.graph.editor_helper_node.call_llm",
        return_value=str(fake_guidance).replace("'", '"'),
    ):
        timeline = generate_timeline("First sentence. Second sentence. Third sentence.")

    assert len(timeline) == 3
    assert timeline[0]["shot_type"] == "b_roll"
    assert timeline[1]["shot_type"] == "talking_head"  # fell back, no guidance for index 1
    assert timeline[2]["shot_type"] == "talking_head"  # fell back, no guidance for index 2


def test_generate_timeline_rejects_invalid_shot_type():
    fake_guidance = [
        {
            "shot_type": "not_a_real_shot_type",
            "camera_angle": "x",
            "onscreen_text": "",
            "resource_suggestion": "",
        }
    ]

    with patch(
        "backend.graph.editor_helper_node.call_llm",
        return_value=str(fake_guidance).replace("'", '"'),
    ):
        timeline = generate_timeline("One sentence here.")

    assert timeline[0]["shot_type"] == "talking_head"  # invalid value replaced with safe default


def test_default_editing_guidance_has_valid_shot_type():
    guidance = _default_editing_guidance()
    assert guidance["shot_type"] == "talking_head"
