from unittest.mock import patch

from backend.graph.rag_node import rag_agent


def test_short_transcript_used_directly_without_retrieval():
    short_text = "This is a short transcript. It has only a few sentences."

    with patch("backend.graph.rag_node.create_transcript_collection") as mock_create:
        result = rag_agent(short_text)

        mock_create.assert_not_called()

    assert result["sources"] == []
    assert result["source_material"] == short_text


def test_long_transcript_triggers_chunking_and_retrieval():
    long_text = "This is a sentence about a topic. " * 100  # well over 400 words

    with (
        patch(
            "backend.graph.rag_node.chunk_text", return_value=["chunk one", "chunk two"]
        ) as mock_chunk,
        patch(
            "backend.graph.rag_node.create_transcript_collection", return_value="fake_collection"
        ) as mock_create,
        patch(
            "backend.graph.rag_node.query_transcript_collection",
            return_value=["relevant chunk one", "relevant chunk two"],
        ) as mock_query,
    ):
        result = rag_agent(long_text, topic="some topic")

        mock_chunk.assert_called_once()
        mock_create.assert_called_once_with(["chunk one", "chunk two"])
        mock_query.assert_called_once_with("fake_collection", "some topic", top_k=5)

    assert result["sources"] == []
    assert "relevant chunk one" in result["source_material"]
    assert "relevant chunk two" in result["source_material"]


def test_long_transcript_uses_default_query_when_no_topic_given():
    long_text = "This is a sentence about a topic. " * 100

    with (
        patch("backend.graph.rag_node.chunk_text", return_value=["chunk one"]),
        patch(
            "backend.graph.rag_node.create_transcript_collection", return_value="fake_collection"
        ),
        patch(
            "backend.graph.rag_node.query_transcript_collection", return_value=["chunk one"]
        ) as mock_query,
    ):
        rag_agent(long_text, topic=None)

        called_query = mock_query.call_args[0][1]
        assert len(called_query) > 0  # some default query string was used, not empty/None
