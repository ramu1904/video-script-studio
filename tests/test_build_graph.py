from unittest.mock import patch

from backend.graph.build_graph import build_graph, route_source


def test_route_source_no_transcript_goes_to_research():
    state = {"topic": "some topic", "transcript": None, "strict_mode": False}
    assert route_source(state) == "research_only"


def test_route_source_transcript_with_strict_mode_goes_to_rag_only():
    state = {"topic": None, "transcript": "some text", "strict_mode": True}
    assert route_source(state) == "rag_only"


def test_route_source_transcript_without_strict_mode_goes_to_rag_and_research():
    state = {"topic": "some topic", "transcript": "some text", "strict_mode": False}
    assert route_source(state) == "rag_and_research"


def test_full_graph_research_only_path():
    fake_research = {
        "source_material": "Some research facts.",
        "sources": [{"title": "x", "url": "y"}],
    }
    fake_fact_check = [
        {"claim": "x", "status": "supported", "explanation": "y", "source_url": None}
    ]
    fake_script = {
        "script": "Final script text.",
        "word_count": 3,
        "estimated_duration_seconds": 1.2,
    }

    with (
        patch("backend.graph.build_graph.research_agent", return_value=fake_research),
        patch("backend.graph.build_graph.fact_check_agent", return_value=fake_fact_check),
        patch("backend.graph.build_graph.write_script", return_value=fake_script),
    ):
        graph = build_graph()
        result = graph.invoke(
            {
                "topic": "some topic",
                "transcript": None,
                "style": "news",
                "duration_seconds": 60,
                "strict_mode": False,
            }
        )

    assert result["script"] == "Final script text."
    assert result["sources"] == [{"title": "x", "url": "y"}]
    assert result["fact_check"] == fake_fact_check


def test_full_graph_rag_only_path_has_no_sources():
    fake_rag = {"source_material": "Some transcript content.", "sources": []}
    fake_fact_check = []
    fake_script = {
        "script": "Script from transcript.",
        "word_count": 3,
        "estimated_duration_seconds": 1.2,
    }

    with (
        patch("backend.graph.build_graph.rag_agent", return_value=fake_rag),
        patch("backend.graph.build_graph.fact_check_agent", return_value=fake_fact_check),
        patch("backend.graph.build_graph.write_script", return_value=fake_script) as mock_write,
    ):
        graph = build_graph()
        result = graph.invoke(
            {
                "topic": None,
                "transcript": "pasted content",
                "style": "neutral",
                "duration_seconds": 30,
                "strict_mode": True,
            }
        )

    assert result["sources"] == []
    assert result["script"] == "Script from transcript."
    mock_write.assert_called_once()


def test_full_graph_rag_and_research_path_merges_source_material():
    fake_rag = {"source_material": "Transcript content.", "sources": []}
    fake_research = {
        "source_material": "Research content.",
        "sources": [{"title": "a", "url": "b"}],
    }
    fake_fact_check = []
    fake_script = {"script": "Merged script.", "word_count": 2, "estimated_duration_seconds": 1.0}

    with (
        patch("backend.graph.build_graph.rag_agent", return_value=fake_rag),
        patch("backend.graph.build_graph.research_agent", return_value=fake_research),
        patch("backend.graph.build_graph.fact_check_agent", return_value=fake_fact_check),
        patch("backend.graph.build_graph.write_script", return_value=fake_script) as mock_write,
    ):
        graph = build_graph()
        graph.invoke(
            {
                "topic": "some topic",
                "transcript": "pasted content",
                "style": "documentary",
                "duration_seconds": 90,
                "strict_mode": False,
            }
        )

    called_source_material = mock_write.call_args.kwargs["source_material"]
    assert "Transcript content." in called_source_material
    assert "Research content." in called_source_material
