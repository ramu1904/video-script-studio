from unittest.mock import patch

from backend.graph.factcheck_node import _parse_json_array, extract_claims


def test_parse_json_array_handles_clean_json():
    result = _parse_json_array('["Claim one.", "Claim two."]')
    assert result == ["Claim one.", "Claim two."]


def test_parse_json_array_strips_markdown_fences():
    result = _parse_json_array('`json\n["Claim one.", "Claim two."]\n`')
    assert result == ["Claim one.", "Claim two."]


def test_parse_json_array_returns_empty_list_on_malformed_input():
    result = _parse_json_array("This is not JSON at all.")
    assert result == []


def test_extract_claims_returns_parsed_claims():
    with patch(
        "backend.graph.factcheck_node.call_llm",
        return_value='["First claim.", "Second claim.", "Third claim."]',
    ):
        claims = extract_claims("Some script text.", max_claims=5)

    assert claims == ["First claim.", "Second claim.", "Third claim."]


def test_extract_claims_respects_max_claims_cap():
    with patch(
        "backend.graph.factcheck_node.call_llm",
        return_value='["One.", "Two.", "Three.", "Four.", "Five."]',
    ):
        claims = extract_claims("Some script text.", max_claims=2)

    assert len(claims) == 2


def test_extract_claims_returns_empty_list_when_llm_response_unparseable():
    with patch("backend.graph.factcheck_node.call_llm", return_value="I cannot help with that."):
        claims = extract_claims("Some script text.")

    assert claims == []
