from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.graph.build_graph import build_graph
from backend.graph.editor_helper_node import generate_timeline
from backend.schemas import (
    FactCheckEntry,
    GenerateScriptRequest,
    GenerateScriptResponse,
    GenerateTimelineRequest,
    GenerateTimelineResponse,
    SourceArticle,
    TimelineEntry,
    duration_to_seconds,
)

app = FastAPI(title="Video Script Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_graph = build_graph()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-script", response_model=GenerateScriptResponse)
def generate_script(request: GenerateScriptRequest):
    try:
        duration_seconds = duration_to_seconds(request.duration, request.custom_duration_seconds)

        initial_state = {
            "topic": request.topic,
            "transcript": request.transcript,
            "style": request.style.value,
            "duration_seconds": duration_seconds,
            "strict_mode": request.strict_mode,
        }

        result = _graph.invoke(initial_state)

        return GenerateScriptResponse(
            script=result["script"],
            word_count=result["word_count"],
            estimated_duration_seconds=result["estimated_duration_seconds"],
            sources=[SourceArticle(**s) for s in result.get("sources", [])],
            fact_check=[FactCheckEntry(**fc) for fc in result.get("fact_check", [])],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-timeline", response_model=GenerateTimelineResponse)
def generate_timeline_endpoint(request: GenerateTimelineRequest):
    try:
        timeline_entries = generate_timeline(request.script)
        return GenerateTimelineResponse(
            timeline=[TimelineEntry(**entry) for entry in timeline_entries]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
