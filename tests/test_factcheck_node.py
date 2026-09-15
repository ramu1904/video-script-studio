from unittest.mock import patch

from backend.graph.factcheck_node import (
    _parse_json_array,
    _parse_json_object,
    extract_claims,
    fact_check_agent,
    verify_claim,
)


def test_parse_json_array_handles_clean_json():
    result = _parse_json_array('["Claim one.", "Claim two."]')
    assert result == ["Claim one.", "Claim two."]


def test_parse_json_array_strips_markdown_fences():
    result = _parse_json_array('`json\n["Claim one.", "Claim two."]\n`')
    assert result == ["Claim one.", "Claim two."]


def test_parse_json_array_returns_empty_list_on_malformed_input():
    result = _parse_json_array("This is not JSON at all.")
    assert result == []


def test_parse_json_object_handles_clean_json():
    result = _parse_json_object('{"status": "supported", "explanation": "x", "source_url": null}')
    assert result == {"status": "supported", "explanation": "x", "source_url": None}


def test_parse_json_object_returns_none_on_malformed_input():
    assert _parse_json_object("Not JSON.") is None


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


def test_verify_claim_returns_unverified_when_no_evidence_found():
    with patch("backend.graph.factcheck_node.search_web", return_value=[]):
        result = verify_claim("Some obscure claim.")

    assert result["status"] == "unverified"
    assert result["source_url"] is None


def test_verify_claim_parses_supported_status_with_source():
    fake_evidence = [{"title": "Article", "snippet": "Confirms the claim.", "url": "https://x.com"}]
    fake_llm_response = (
        '{"status": "supported", "explanation": "Confirmed by evidence.", '
        '"source_url": "https://x.com"}'
    )

    with (
        patch("backend.graph.factcheck_node.search_web", return_value=fake_evidence),
        patch("backend.graph.factcheck_node.call_llm", return_value=fake_llm_response),
    ):
        result = verify_claim("Some claim.")

    assert result["status"] == "supported"
    assert result["source_url"] == "https://x.com"


def test_verify_claim_falls_back_to_unverified_on_unparseable_llm_response():
    fake_evidence = [{"title": "Article", "snippet": "Some text.", "url": "https://x.com"}]

    with (
        patch("backend.graph.factcheck_node.search_web", return_value=fake_evidence),
        patch("backend.graph.factcheck_node.call_llm", return_value="not valid json"),
    ):
        result = verify_claim("Some claim.")

    assert result["status"] == "unverified"


def test_verify_claim_falls_back_to_unverified_on_invalid_status_value():
    fake_evidence = [{"title": "Article", "snippet": "Some text.", "url": "https://x.com"}]
    fake_llm_response = '{"status": "definitely_true", "explanation": "x", "source_url": null}'

    with (
        patch("backend.graph.factcheck_node.search_web", return_value=fake_evidence),
        patch("backend.graph.factcheck_node.call_llm", return_value=fake_llm_response),
    ):
        result = verify_claim("Some claim.")

    assert result["status"] == "unverified"


def test_fact_check_agent_extracts_and_verifies_each_claim():
    with (
        patch("backend.graph.factcheck_node.extract_claims", return_value=["Claim A.", "Claim B."]),
        patch(
            "backend.graph.factcheck_node.verify_claim",
            side_effect=lambda claim, **kwargs: {
                "claim": claim,
                "status": "supported",
                "explanation": "x",
                "source_url": None,
            },
        ) as mock_verify,
    ):
        results = fact_check_agent("Some script.", max_claims=2)

    assert len(results) == 2
    assert mock_verify.call_count == 2
    assert results[0]["claim"] == "Claim A."
    assert results[1]["claim"] == "Claim B."
