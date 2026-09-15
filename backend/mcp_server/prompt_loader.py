from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"

_WORDS_PER_MINUTE = 150


def calculate_word_target(duration_seconds: int) -> int:
    """Estimate a natural spoken-word count for a given duration,
    based on an average speaking pace of 150 words/minute."""
    return round((duration_seconds / 60) * _WORDS_PER_MINUTE)


def load_prompt_template(
    style: str, topic: str, source_material: str, duration_seconds: int
) -> str:
    """Load a style's prompt template and fill in the topic, source material,
    duration, and calculated word target."""
    template_path = _PROMPTS_DIR / f"style_{style}.txt"
    if not template_path.exists():
        raise ValueError(f"No prompt template found for style '{style}'")

    template_text = template_path.read_text(encoding="utf-8")
    word_target = calculate_word_target(duration_seconds)

    return template_text.format(
        topic=topic,
        source_material=source_material,
        duration_seconds=duration_seconds,
        word_target=word_target,
    )
