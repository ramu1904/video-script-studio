from unittest.mock import patch

from backend.mcp_server.server import ingest_transcript_tool
from backend.mcp_server.transcript_resource_store import get_chunk, list_chunk_ids


def test_ingest_transcript_tool_caches_chunks():
    fake_rag_result = {"sources": [], "source_material": "chunk one text\n\nchunk two text"}

    with patch("backend.mcp_server.server.rag_agent", return_value=fake_rag_result):
        result = ingest_transcript_tool("some transcript", topic="some topic")

    assert len(result["chunk_resource_ids"]) == 2
    first_chunk_id = result["chunk_resource_ids"][0]
    assert get_chunk(first_chunk_id) == "chunk one text"


def test_ingest_transcript_tool_skips_empty_chunks():
    fake_rag_result = {"sources": [], "source_material": "only one real chunk\n\n"}

    with patch("backend.mcp_server.server.rag_agent", return_value=fake_rag_result):
        result = ingest_transcript_tool("some transcript")

    assert len(result["chunk_resource_ids"]) == 1


def test_ingest_transcript_tool_passes_topic_to_rag_agent():
    fake_rag_result = {"sources": [], "source_material": "text"}

    with patch("backend.mcp_server.server.rag_agent", return_value=fake_rag_result) as mock_rag:
        ingest_transcript_tool("some transcript", topic="my topic")

        mock_rag.assert_called_once_with("some transcript", topic="my topic")


def test_read_cached_transcript_chunk_returns_text():
    from backend.mcp_server.server import read_cached_transcript_chunk
    from backend.mcp_server.transcript_resource_store import store_chunk

    chunk_id = store_chunk("Some cached chunk content.")

    content = read_cached_transcript_chunk(chunk_id)

    assert content == "Some cached chunk content."


def test_read_cached_transcript_chunk_handles_missing_id():
    from backend.mcp_server.server import read_cached_transcript_chunk

    content = read_cached_transcript_chunk("nonexistent-id")

    assert "No cached transcript chunk found" in content
