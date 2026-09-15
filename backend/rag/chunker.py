import re


def _split_into_sentences(text: str) -> list[str]:
    """Rough sentence splitter based on punctuation followed by whitespace."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(text: str, target_words: int = 150, overlap_sentences: int = 1) -> list[str]:
    """Split text into chunks of roughly target_words words, grouped by whole
    sentences (never cutting mid-sentence), with a small overlap between
    consecutive chunks to preserve context across chunk boundaries."""
    sentences = _split_into_sentences(text)
    if not sentences:
        return []

    chunks = []
    current_sentences: list[str] = []
    current_word_count = 0

    for sentence in sentences:
        current_sentences.append(sentence)
        current_word_count += len(sentence.split())

        if current_word_count >= target_words:
            chunks.append(" ".join(current_sentences))
            overlap = current_sentences[-overlap_sentences:] if overlap_sentences > 0 else []
            current_sentences = list(overlap)
            current_word_count = sum(len(s.split()) for s in current_sentences)

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks
