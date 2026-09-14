import pytest
from pydantic import ValidationError

from backend.schemas import (
    Duration,
    GenerateScriptRequest,
    Style,
)


def test_valid_request_with_topic():
    req = GenerateScriptRequest(
        topic="Fake medicines racket in Bangalore",
        duration=Duration.SEC_60,
        style=Style.NEWS,
    )
    assert req.topic == "Fake medicines racket in Bangalore"
    assert req.strict_mode is False


def test_valid_request_with_transcript_only():
    req = GenerateScriptRequest(
        transcript="Some pasted content here",
        duration=Duration.MIN_3,
        style=Style.DOCUMENTARY,
    )
    assert req.transcript is not None
    assert req.topic is None


def test_rejects_when_neither_topic_nor_transcript():
    with pytest.raises(ValidationError):
        GenerateScriptRequest(duration=Duration.SEC_30, style=Style.NEUTRAL)


def test_custom_duration_requires_seconds():
    with pytest.raises(ValidationError):
        GenerateScriptRequest(
            topic="Some topic",
            duration=Duration.CUSTOM,
            style=Style.NEWS,
            # custom_duration_seconds missing on purpose
        )


def test_custom_duration_with_seconds_is_valid():
    req = GenerateScriptRequest(
        topic="Some topic",
        duration=Duration.CUSTOM,
        style=Style.NEWS,
        custom_duration_seconds=45,
    )
    assert req.custom_duration_seconds == 45
