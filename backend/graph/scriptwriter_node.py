import re

from backend.llm import call_llm
from backend.mcp_server.prompt_loader import calculate_word_target, load_prompt_template


_TOKENS_PER_WORD_BUFFER = 1.9
_MIN_MAX_TOKENS = 200
_TRIM_TOLERANCE = 1.15  # allow up to 15% over target before trimming, for a clean sentence ending


def _clean_script_output(text: str) -> str:
    """Strip any title/note/formatting artifacts that slipped through despite
    the prompt's output rules, so what's left is pure spoken narration."""
    cleaned = text.strip()

    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*(.*?)\*", r"\1", cleaned)
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"`.*?`", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\[.*?\]", "", cleaned)
    cleaned = re.sub(r"^\(Note[^)]*\)\s*", "", cleaned, flags=re.MULTILINE | re.IGNORECASE)
    cleaned = re.sub(r"^\(This script[^)]*\)\s*", "", cleaned, flags=re.MULTILINE | re.IGNORECASE)
    cleaned = re.sub(r"^Title:.*$", "", cleaned, flags=re.MULTILINE | re.IGNORECASE)
    cleaned = re.sub(r"^-{3,}\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def _split_into_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _trim_to_word_target(text: str, word_target: int, tolerance: float = _TRIM_TOLERANCE) -> str:
    """Deterministically trim generated text down to close to word_target,
    always stopping at a complete sentence boundary - never trusting the
    model's own length judgment, since small models reliably overshoot
    length instructions regardless of how the prompt is worded."""
    max_words = word_target * tolerance
    sentences = _split_into_sentences(text)

    result_sentences: list[str] = []
    word_count = 0

    for sentence in sentences:
        sentence_word_count = len(sentence.split())

        if result_sentences and word_count + sentence_word_count > max_words:
            break

        result_sentences.append(sentence)
        word_count += sentence_word_count

        if word_count >= word_target:
            break

    return " ".join(result_sentences)


def write_script(topic: str, source_material: str, style: str, duration_seconds: int) -> dict:
    """Generate the final teleprompter-ready script using the given style
    template and source material, sized to the target duration. Length is
    enforced deterministically after generation, not left to the model."""

    prompt = load_prompt_template(style, topic, source_material, duration_seconds)

    word_target = calculate_word_target(duration_seconds)
    max_tokens = max(_MIN_MAX_TOKENS, int(word_target * _TOKENS_PER_WORD_BUFFER * 1.3))

    raw_output = call_llm(prompt=prompt, temperature=0.7, max_tokens=max_tokens)
    script = _clean_script_output(raw_output)
    script = _trim_to_word_target(script, word_target)

    word_count = len(script.split())
    estimated_duration_seconds = round((word_count / 150) * 60, 1)

    return {
        "script": script,
        "word_count": word_count,
        "estimated_duration_seconds": estimated_duration_seconds,
    }
