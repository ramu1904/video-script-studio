import json
import re

from backend.llm import call_llm

_WORDS_PER_SECOND = 150 / 60  # matches the speaking pace used elsewhere in the project

_VALID_SHOT_TYPES = {"talking_head", "b_roll", "text_overlay", "image_cutaway", "archive_footage"}

_TIMELINE_SYSTEM_PROMPT = (
    "You are a video editing assistant. You will be given a numbered list of "
    "narration sentences from a video script. For EACH sentence, suggest editing "
    "guidance: what shot type to use, the camera angle, any on-screen text overlay, "
    "and a resource suggestion (what footage/image to show).\n\n"
    "Respond with ONLY a JSON array, one object per sentence, in the SAME ORDER, "
    "same length as the input. No markdown fences, no explanation. Each object must "
    "have exactly these fields:\n"
    '{"shot_type": "one of: talking_head, b_roll, text_overlay, image_cutaway, archive_footage", '
    '"camera_angle": "short phrase, e.g. close-up on host, wide shot of location", '
    '"onscreen_text": "short on-screen caption, or empty string if none needed", '
    '"resource_suggestion": "short suggestion of what footage or image to use"}'
)


def _split_into_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _parse_json_array(raw_text: str) -> list[dict]:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^`(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*`$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    return []


def _default_editing_guidance() -> dict:
    """Safe fallback when the LLM response can't be parsed or is incomplete,
    so the timeline is always fully populated even in a degraded state."""
    return {
        "shot_type": "talking_head",
        "camera_angle": "medium shot",
        "onscreen_text": "",
        "resource_suggestion": "",
    }


def generate_timeline(script: str) -> list[dict]:
    """Break a finished script into a timestamped, shot-by-shot editing
    timeline. Timing is calculated deterministically from word counts;
    editing guidance (shot type, angle, on-screen text, resources) comes
    from a single LLM call covering the whole script at once."""

    sentences = _split_into_sentences(script)
    if not sentences:
        return []

    numbered_list = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(sentences))
    prompt = f"Narration sentences:\n{numbered_list}"

    response = call_llm(
        prompt=prompt,
        system_prompt=_TIMELINE_SYSTEM_PROMPT,
        temperature=0.4,
        max_tokens=1000,
    )

    guidance_list = _parse_json_array(response)

    timeline = []
    running_time = 0.0

    for i, sentence in enumerate(sentences):
        word_count = len(sentence.split())
        duration = word_count / _WORDS_PER_SECOND
        start = round(running_time, 1)
        end = round(running_time + duration, 1)
        running_time = end

        guidance = guidance_list[i] if i < len(guidance_list) else {}
        if not isinstance(guidance, dict) or guidance.get("shot_type") not in _VALID_SHOT_TYPES:
            guidance = _default_editing_guidance()

        timeline.append(
            {
                "start_seconds": start,
                "end_seconds": end,
                "voiceover_chunk": sentence,
                "shot_type": guidance.get("shot_type", "talking_head"),
                "camera_angle": guidance.get("camera_angle", "medium shot"),
                "onscreen_text": guidance.get("onscreen_text") or None,
                "resource_suggestion": guidance.get("resource_suggestion") or None,
            }
        )

    return timeline
