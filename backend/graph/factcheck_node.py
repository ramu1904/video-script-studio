import json
import re

from backend.llm import call_llm
from backend.mcp_server.search_functions import search_web

_VALID_STATUSES = {"supported", "uncertain", "unverified"}

_EXTRACT_CLAIMS_SYSTEM_PROMPT = (
    "You are a fact-checking assistant. Given a video script, identify the key "
    "factual claims it makes - specific, checkable statements about events, "
    "numbers, people, or actions (not opinions or stylistic flourishes). "
    "Respond with ONLY a JSON array of strings, nothing else. No markdown code "
    'fences, no explanation. Example format: ["Claim one here.", "Claim two here."]'
)

_VERIFY_CLAIM_SYSTEM_PROMPT = (
    "You are a fact-checking assistant. You will be given a claim and some "
    "search result snippets found about it. Judge whether the claim is "
    "supported by the evidence.\n\n"
    "Respond with ONLY a JSON object, nothing else, in this exact format: "
    '{"status": "supported", "explanation": "brief reason", "source_url": "url or null"}\n\n'
    "status must be exactly one of: supported, uncertain, unverified.\n"
    "- supported: the evidence clearly confirms the claim\n"
    "- uncertain: the evidence is related but doesn't clearly confirm or deny it\n"
    "- unverified: no relevant evidence was found\n"
    "source_url should be the single most relevant URL from the evidence, or null if none applies."
)


def _parse_json_array(raw_text: str) -> list[str]:
    """Extract a JSON array of strings from LLM output, tolerating minor
    formatting mistakes like markdown code fences around the JSON."""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^`(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*`$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except json.JSONDecodeError:
        pass

    return []


def _parse_json_object(raw_text: str) -> dict | None:
    """Extract a JSON object from LLM output, tolerating markdown code fences."""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^`(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*`$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    return None


def extract_claims(script_text: str, max_claims: int = 5) -> list[str]:
    """Ask the LLM to identify the key checkable factual claims in a script."""
    prompt = f"Script:\n{script_text}\n\nExtract up to {max_claims} key factual claims."

    response = call_llm(
        prompt=prompt,
        system_prompt=_EXTRACT_CLAIMS_SYSTEM_PROMPT,
        temperature=0.2,
        max_tokens=400,
    )

    claims = _parse_json_array(response)
    return claims[:max_claims]


def verify_claim(claim: str, max_evidence: int = 3) -> dict:
    """Search the web for evidence about a claim, then ask the LLM to judge
    whether the claim is supported, uncertain, or unverified."""
    evidence = search_web(claim, max_results=max_evidence)

    if not evidence:
        return {
            "claim": claim,
            "status": "unverified",
            "explanation": "No relevant search results were found for this claim.",
            "source_url": None,
        }

    evidence_text = "\n".join(
        f"- {item.get('title')}: {item.get('snippet')} (URL: {item.get('url')})"
        for item in evidence
    )
    prompt = f"Claim: {claim}\n\nEvidence found:\n{evidence_text}"

    response = call_llm(
        prompt=prompt,
        system_prompt=_VERIFY_CLAIM_SYSTEM_PROMPT,
        temperature=0.2,
        max_tokens=200,
    )

    parsed = _parse_json_object(response)

    if parsed is None or parsed.get("status") not in _VALID_STATUSES:
        return {
            "claim": claim,
            "status": "unverified",
            "explanation": "Could not determine verification status from available evidence.",
            "source_url": None,
        }

    source_url = parsed.get("source_url")
    if source_url in (None, "null", ""):
        source_url = None

    return {
        "claim": claim,
        "status": parsed["status"],
        "explanation": parsed.get("explanation", ""),
        "source_url": source_url,
    }


def fact_check_agent(script_text: str, max_claims: int = 5) -> list[dict]:
    """Full fact-check pipeline: extract the key claims from a script, then
    verify each one against live search evidence. Always runs regardless of
    strict_mode - this only verifies existing claims, it never adds new
    content to the script."""
    claims = extract_claims(script_text, max_claims=max_claims)
    return [verify_claim(claim) for claim in claims]
