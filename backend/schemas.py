from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums — fixed choices used across requests
# ---------------------------------------------------------------------------


class Duration(str, Enum):
    SEC_30 = "30s"
    SEC_60 = "60s"
    SEC_90 = "90s"
    MIN_3 = "3min"
    MIN_8 = "8min"
    CUSTOM = "custom"


class Style(str, Enum):
    NEWS = "news"
    CURIOSITY = "curiosity"
    DOCUMENTARY = "documentary"
    STORYTELLING = "storytelling"
    DRAMATIC = "dramatic"
    HORROR = "horror"
    MOTIVATIONAL = "motivational"
    COMEDIC = "comedic"
    NEUTRAL = "neutral"


class FactCheckStatus(str, Enum):
    SUPPORTED = "supported"
    UNCERTAIN = "uncertain"
    UNVERIFIED = "unverified"


class ShotType(str, Enum):
    TALKING_HEAD = "talking_head"
    B_ROLL = "b_roll"
    TEXT_OVERLAY = "text_overlay"
    IMAGE_CUTAWAY = "image_cutaway"
    ARCHIVE_FOOTAGE = "archive_footage"


# ---------------------------------------------------------------------------
# Shared building-block models
# ---------------------------------------------------------------------------


class SourceArticle(BaseModel):
    title: str
    url: str
    published_date: Optional[str] = None
    snippet: Optional[str] = None
    image_url: Optional[str] = None


class FactCheckEntry(BaseModel):
    claim: str
    status: FactCheckStatus
    explanation: str
    source_url: Optional[str] = None


class TimelineEntry(BaseModel):
    start_seconds: float
    end_seconds: float
    voiceover_chunk: str
    shot_type: ShotType
    camera_angle: str
    onscreen_text: Optional[str] = None
    resource_suggestion: Optional[str] = None


# ---------------------------------------------------------------------------
# /generate-script
# ---------------------------------------------------------------------------


class GenerateScriptRequest(BaseModel):
    topic: Optional[str] = Field(default=None, description="News/topic to research")
    transcript: Optional[str] = Field(default=None, description="User-pasted content for RAG")
    duration: Duration
    style: Style
    strict_mode: bool = Field(
        default=False,
        description="If True and transcript is given, use ONLY the transcript "
        "for script content (no new web research). Fact-checking still always runs.",
    )
    custom_duration_seconds: Optional[int] = Field(
        default=None, description="Required only when duration == CUSTOM"
    )

    @model_validator(mode="after")
    def check_inputs(self) -> "GenerateScriptRequest":
        if not self.topic and not self.transcript:
            raise ValueError("Provide at least one of: topic, transcript")
        if self.duration == Duration.CUSTOM and not self.custom_duration_seconds:
            raise ValueError("custom_duration_seconds is required when duration is 'custom'")
        return self


class GenerateScriptResponse(BaseModel):
    script: str
    word_count: int
    estimated_duration_seconds: float
    sources: List[SourceArticle] = Field(default_factory=list)
    fact_check: List[FactCheckEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# /generate-timeline
# ---------------------------------------------------------------------------


class GenerateTimelineRequest(BaseModel):
    script: str
    duration: Duration
    custom_duration_seconds: Optional[int] = None


class GenerateTimelineResponse(BaseModel):
    timeline: List[TimelineEntry]
