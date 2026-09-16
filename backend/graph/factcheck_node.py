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
    "source_url must be copied EXACTLY, character-for-character, from one of the "
    "evidence URLs provided below. Never invent, guess, modify, or construct a URL "
    "that was not given to you. If no evidence URL applies, use null."
)


def _extract_claim_text(item) -> str:
    """A claim item may be a plain string (the requested format) or a dict
    like {"claim": "...", "source": "...", ...} (a common small-model
    deviation). Pull out the actual claim text either way."""
    if isinstance(item, str):
        return item.strip()

    if isinstance(item, dict):
        for key in ("claim", "text", "statement"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for value in item.values():
            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""


def _find_individual_json_objects(text: str) -> list[dict]:
    """Last-resort fallback: hunt for standalone {...} objects anywhere in
    the text, regardless of how they are wrapped, nested in separate arrays,
    concatenated without commas, or otherwise malformed as a whole document.
    Small models frequently break the requested single-array format in
    inconsistent ways, but usually still emit valid individual JSON objects -
    this recovers claims from those regardless of the outer structure.
    Assumes claim objects are flat (no nested braces)."""
    objects = []
    for match in re.finditer(r"\{[^{}]+\}", text):
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                objects.append(parsed)
        except json.JSONDecodeError:
            continue
    return objects


def _parse_json_array(raw_text: str) -> list[str]:
    """Extract a list of claim strings from LLM output. Tries a clean parse
    first, then increasingly forgiving fallbacks, since small models produce
    a wide variety of malformed variations on the requested JSON array format."""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^`(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*`$", "", cleaned)

    working = cleaned
    for _ in range(3):
        try:
            parsed = json.loads(working)
            if isinstance(parsed, list):
                claims = [_extract_claim_text(item) for item in parsed]
                claims = [c for c in claims if c]
                if claims:
                    return claims
        except json.JSONDecodeError:
            pass

        if working.count("[") > working.count("]") and working.startswith("["):
            working = working[1:].strip()
            continue

        break

    found_objects = _find_individual_json_objects(cleaned)
    if found_objects:
        claims = [_extract_claim_text(obj) for obj in found_objects]
        return [c for c in claims if c]

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
    whether the claim is supported, uncertain, or unverified. The returned
    source_url is validated against the real evidence URLs - if the model
    fabricates a URL that wasn't actually in the evidence, it is discarded
    rather than presented as if it were real."""
    evidence = search_web(claim, max_results=max_evidence)

    if not evidence:
        return {
            "claim": claim,
            "status": "unverified",
            "explanation": "No relevant search results were found for this claim.",
            "source_url": None,
        }

    evidence_urls = {item.get("url") for item in evidence if item.get("url")}

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
    if source_url in (None, "null", "") or source_url not in evidence_urls:
        source_url = None

    return {
        "claim": claim,
        "status": parsed["status"],
        "explanation": parsed.get("explanation", ""),
        "source_url": source_url,
    }


def fact_check_agent(script_text: str, max_claims: int = 5) -> list[dict]:
    """Full fact-check pipeline: extract the key claims from a script, then
    verify each one against live search evidence."""
    claims = extract_claims(script_text, max_claims=max_claims)
    return [verify_claim(claim) for claim in claims]
