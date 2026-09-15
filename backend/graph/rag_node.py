from backend.rag.chunker import chunk_text
from backend.rag.vector_store import create_transcript_collection, query_transcript_collection


_SHORT_TRANSCRIPT_WORD_LIMIT = 400  # below this, skip retrieval and use the whole transcript
_DEFAULT_RETRIEVAL_QUERY = "the main topic, key facts, and important information in this content"


def rag_agent(transcript: str, topic: str | None = None, top_k: int = 5) -> dict:
    """Given a user-pasted transcript (and an optional topic to focus retrieval),
    return source_material for the Script Writer. Short transcripts are used
    directly; longer ones are chunked, embedded, and the most relevant chunks
    retrieved via semantic search. Mirrors research_agent's return shape."""

    word_count = len(transcript.split())

    if word_count <= _SHORT_TRANSCRIPT_WORD_LIMIT:
        return {
            "sources": [],
            "source_material": transcript.strip(),
        }

    chunks = chunk_text(transcript, target_words=150, overlap_sentences=1)
    collection_name = create_transcript_collection(chunks)

    query = topic if topic else _DEFAULT_RETRIEVAL_QUERY
    relevant_chunks = query_transcript_collection(collection_name, query, top_k=top_k)

    source_material = "\n\n".join(relevant_chunks)

    return {
        "sources": [],
        "source_material": source_material,
    }
