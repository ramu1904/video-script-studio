import json
import re

from backend.llm import call_llm

_EXTRACT_CLAIMS_SYSTEM_PROMPT = (
    "You are a fact-checking assistant. Given a video script, identify the key "
    "factual claims it makes - specific, checkable statements about events, "
    "numbers, people, or actions (not opinions or stylistic flourishes). "
    "Respond with ONLY a JSON array of strings, nothing else. No markdown code "
    'fences, no explanation. Example format: ["Claim one here.", "Claim two here."]'
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
