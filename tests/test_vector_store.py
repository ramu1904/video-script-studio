from backend.rag.vector_store import create_transcript_collection, query_transcript_collection


def test_create_and_query_transcript_collection_returns_relevant_chunks():
    chunks = [
        "The pharmacy owner Veeresh Kumar Jain was arrested by the SIT team.",
        "The weather in Bangalore has been pleasant this September.",
        "Investigators found fake cancer drugs supplied to over 90 hospitals.",
        "Traffic congestion on Outer Ring Road has worsened recently.",
    ]

    collection_name = create_transcript_collection(chunks)
    results = query_transcript_collection(
        collection_name, "counterfeit medicine investigation", top_k=2
    )

    assert len(results) == 2
    assert any("cancer drugs" in r or "pharmacy owner" in r for r in results)
    assert not any("weather" in r or "Traffic" in r for r in results)


def test_collection_names_are_unique():
    chunks = ["Some sample text here."]

    name1 = create_transcript_collection(chunks)
    name2 = create_transcript_collection(chunks)

    assert name1 != name2


def test_query_respects_top_k():
    chunks = [f"This is sentence number {i} about various topics." for i in range(10)]
    collection_name = create_transcript_collection(chunks)

    results = query_transcript_collection(collection_name, "sentence topics", top_k=3)

    assert len(results) == 3
