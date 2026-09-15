from backend.rag.chunker import chunk_text


def test_chunk_text_empty_string_returns_empty_list():
    assert chunk_text("") == []


def test_chunk_text_short_text_returns_single_chunk():
    text = "This is one short sentence. Here is another one."
    chunks = chunk_text(text, target_words=100)
    assert len(chunks) == 1


def test_chunk_text_never_cuts_mid_sentence():
    text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here."
    chunks = chunk_text(text, target_words=8, overlap_sentences=0)
    for chunk in chunks:
        assert chunk.strip().endswith(".")


def test_chunk_text_applies_overlap_between_chunks():
    text = (
        "Sentence one is here. Sentence two is here. Sentence three is here. Sentence four is here."
    )
    chunks = chunk_text(text, target_words=8, overlap_sentences=1)
    # the last sentence of chunk 1 should also appear at the start of chunk 2
    assert len(chunks) >= 2
    last_sentence_of_chunk1 = chunks[0].split(". ")[-1]
    assert chunks[1].startswith(last_sentence_of_chunk1.split(".")[0])


def test_chunk_text_produces_multiple_chunks_for_long_text():
    text = " ".join([f"This is sentence number {i}." for i in range(20)])
    chunks = chunk_text(text, target_words=20, overlap_sentences=1)
    assert len(chunks) > 1
