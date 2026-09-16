from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.graph.factcheck_node import fact_check_agent
from backend.graph.rag_node import rag_agent
from backend.graph.research_node import research_agent
from backend.graph.scriptwriter_node import write_script


class ScriptGraphState(TypedDict):
    topic: Optional[str]
    transcript: Optional[str]
    style: str
    duration_seconds: int
    strict_mode: bool
    source_material: str
    sources: list
    fact_check: list
    script: str
    word_count: int
    estimated_duration_seconds: float


def route_source(state: ScriptGraphState) -> str:
    """Decide which source-gathering path to take based on what the user
    provided and whether strict_mode is on."""
    if state.get("transcript"):
        return "rag_only" if state.get("strict_mode") else "rag_and_research"
    return "research_only"


def research_only_node(state: ScriptGraphState) -> dict:
    result = research_agent(state["topic"])
    return {"source_material": result["source_material"], "sources": result["sources"]}


def rag_only_node(state: ScriptGraphState) -> dict:
    result = rag_agent(state["transcript"], topic=state.get("topic"))
    return {"source_material": result["source_material"], "sources": []}


def rag_and_research_node(state: ScriptGraphState) -> dict:
    rag_result = rag_agent(state["transcript"], topic=state.get("topic"))
    combined_material = rag_result["source_material"]
    sources = []

    if state.get("topic"):
        research_result = research_agent(state["topic"])
        if research_result["source_material"]:
            combined_material += "\n\n" + research_result["source_material"]
        sources = research_result["sources"]

    return {"source_material": combined_material, "sources": sources}


def fact_check_graph_node(state: ScriptGraphState) -> dict:
    results = fact_check_agent(state["source_material"], max_claims=5)
    return {"fact_check": results}


def script_writer_graph_node(state: ScriptGraphState) -> dict:
    result = write_script(
        topic=state.get("topic") or "the provided content",
        source_material=state["source_material"],
        style=state["style"],
        duration_seconds=state["duration_seconds"],
    )
    return {
        "script": result["script"],
        "word_count": result["word_count"],
        "estimated_duration_seconds": result["estimated_duration_seconds"],
    }


def build_graph():
    graph = StateGraph(ScriptGraphState)

    graph.add_node("research_only", research_only_node)
    graph.add_node("rag_only", rag_only_node)
    graph.add_node("rag_and_research", rag_and_research_node)
    graph.add_node("fact_check_step", fact_check_graph_node)
    graph.add_node("script_writer", script_writer_graph_node)

    graph.add_conditional_edges(
        START,
        route_source,
        {
            "research_only": "research_only",
            "rag_only": "rag_only",
            "rag_and_research": "rag_and_research",
        },
    )

    graph.add_edge("research_only", "fact_check_step")
    graph.add_edge("rag_only", "fact_check_step")
    graph.add_edge("rag_and_research", "fact_check_step")
    graph.add_edge("fact_check_step", "script_writer")
    graph.add_edge("script_writer", END)

    return graph.compile()
